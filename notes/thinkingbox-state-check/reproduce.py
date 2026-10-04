"""Replay one pinned ThinkingBox validator with synthetic effect inputs.

No agent, database, MCP server, framework package, or model is run.
Upstream Python is Microsoft MIT-licensed; see LICENSE.upstream.txt.
"""

import ast
import hashlib
import json
from types import SimpleNamespace
from urllib.request import Request, urlopen


COMMIT = "fcaba4c1a9debec42fda7f15bf29fe6d6b46c431"
SOURCE = (
    "https://raw.githubusercontent.com/microsoft/thinkingbox-data/"
    + COMMIT
    + "/dataset/test_case/sandbox_external_retail/sandbox_external_retail_group1.py"
)
SHA256 = "9a3bc8a7bfbe6aab60ba1f6c2bd7e57719524a9cccc9b2528d64ca832f6e943d"
TARGET = "test_case_ST003_006"


def main():
    with urlopen(Request(SOURCE, headers={"User-Agent": "thinkingbox-validator-example"}), timeout=30) as response:
        raw = response.read(1_000_001)
    if len(raw) > 1_000_000 or hashlib.sha256(raw).hexdigest() != SHA256:
        raise RuntimeError("Pinned upstream source does not match the recorded SHA-256")

    tree = ast.parse(raw.decode("utf-8"))
    names = {"validate_database", TARGET}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != names or len(functions) != 2:
        raise RuntimeError("Expected validator and target function were not found")
    target = next(node for node in functions if node.name == TARGET)
    target_body = target.body[1:]
    if ast.dump(ast.Module(body=target_body, type_ignores=[])) != ast.dump(
        ast.parse("validate_database(x)")
    ):
        raise RuntimeError("Target no longer delegates only to validate_database")

    # The task docstring contains the synthetic scenario. Its executable body
    # and the validator are unchanged. No other upstream code is imported.
    target.body = target_body
    module = ast.Module(
        body=ast.parse("from __future__ import annotations").body + functions,
        type_ignores=[],
    )
    namespace = {"json": json}
    exec(compile(ast.fix_missing_locations(module), "<pinned-thinkingbox-validator>", "exec", optimize=0), namespace)

    cases = [
        ("equal supplied hashes", "synthetic-same", "synthetic-same", [], "accepts"),
        (
            "solved versus hold diagnostic",
            "synthetic-different",
            "synthetic-same",
            [{"path": "tickets/example/status", "type": "change", "result": "solved", "golden": "hold"}],
            "rejects",
        ),
        ("unequal hashes with no diff", "synthetic-different", "synthetic-same", [], "rejects"),
        (
            "hold status plus an extra-effect diagnostic",
            "synthetic-different",
            "synthetic-same",
            [{"path": "refunds/extra-example", "type": "added", "result": {"ticket_status": "hold"}, "golden": None}],
            "rejects",
        ),
    ]
    print("Pinned task: " + TARGET)
    print("Scope: supplied synthetic effects; validator only")
    for label, result_hash, golden_hash, diff, expected in cases:
        context = SimpleNamespace(effects={"sandbox_external_retail": {
            "result_db_hash": result_hash, "golden_db_hash": golden_hash, "diff": diff,
        }})
        try:
            namespace[TARGET](context, None)
            outcome = "accepts"
        except AssertionError as error:
            if "Database hash after test execution" not in str(error):
                raise
            outcome = "rejects"
        if outcome != expected:
            raise RuntimeError(label + ": unexpected validator result " + outcome)
        print(label + ": " + outcome)


if __name__ == "__main__":
    main()
