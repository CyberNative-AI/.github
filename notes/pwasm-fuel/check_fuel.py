"""Two authored tiny Wasm modules: count fuel without timing claims.

Copyright 2026 CyberNative AI LLC. SPDX-License-Identifier: MIT
Requires the pwasm 0.2a0 distribution, Python 3.10+.
"""

import importlib.metadata
import json
import platform
import time

from pwasm import OutOfFuel, Timeout, decode_module, instantiate
from pwasm.runtime import Limits


def uleb(value):
    result = bytearray()
    while True:
        part = value & 0x7F
        value >>= 7
        result.append(part | (0x80 if value else 0))
        if not value:
            return bytes(result)


def section(number, payload):
    return bytes([number]) + uleb(len(payload)) + payload


def module_bytes(additions):
    # (func (export "run") (param $n i32) (result i32) (local $sum i32)
    #   (block $exit (loop $again
    #     (br_if $exit (i32.eqz (local.get $n)))
    #     ;; repeat: sum = sum + 1
    #     (local.set $n (i32.sub (local.get $n) (i32.const 1)))
    #     (br $again))) (local.get $sum))
    increment = bytes.fromhex("20 01 41 01 6a 21 01")
    code = (
        bytes.fromhex("01 01 7f 02 40 03 40 20 00 45 0d 01")
        + increment * additions
        + bytes.fromhex("20 00 41 01 6b 21 00 0c 00 0b 0b 20 01 0b")
    )
    return (
        b"\x00asm\x01\x00\x00\x00"
        + section(1, bytes.fromhex("01 60 01 7f 01 7f"))
        + section(3, bytes.fromhex("01 00"))
        + section(7, b"\x01\x03run\x00\x00")
        + section(10, b"\x01" + uleb(len(code)) + code)
    )


def main():
    version = importlib.metadata.version("pwasm")
    assert version == "0.2a0", f"Expected distribution 0.2a0, found {version}"
    rows = []
    controls = []
    for mode in ("interpret", "compile", "auto"):
        for additions in (1, 65):
            wasm = module_bytes(additions)
            limits = Limits(fuel=1000, check_interval=1)
            instance = instantiate(decode_module(wasm), limits=limits, mode=mode)
            for call in range(1, 4):
                before = limits.fuel_consumed
                result = instance.exports.run(10)
                used = limits.fuel_consumed - before
                assert result == 10 * additions, (mode, additions, result)
                assert used == 12, (mode, additions, used)
                rows.append({"mode": mode, "additions_per_iteration": additions,
                             "call": call, "result": result, "fuel": used})

            exhausted = Limits(fuel=5, check_interval=1)
            control = instantiate(decode_module(wasm), limits=exhausted, mode=mode)
            try:
                control.exports.run(10)
            except OutOfFuel:
                assert exhausted.fuel_consumed == 5
                controls.append({"mode": mode, "additions_per_iteration": additions,
                                 "control": "fuel=5", "outcome": "OutOfFuel", "fuel": 5})
            else:
                raise AssertionError("Expected OutOfFuel")

        deadline = Limits(fuel=1000, check_interval=1)
        deadline.set_deadline(time.monotonic() - 1)
        control = instantiate(decode_module(module_bytes(1)), limits=deadline, mode=mode)
        try:
            control.exports.run(10)
        except Timeout:
            controls.append({"mode": mode, "control": "expired deadline", "outcome": "Timeout"})
        else:
            raise AssertionError("Expected Timeout")

    print(json.dumps({"distribution": "pwasm", "version": version,
                      "python": platform.python_version(), "system": platform.system(),
                      "rows": rows, "controls": controls,
                      "scope": "authored tiny modules; no guest interpreters, host imports, memory, speed or security audit"},
                     indent=2))


if __name__ == "__main__":
    main()
