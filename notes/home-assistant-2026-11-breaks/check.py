"""Replay the failing operations against the Home Assistant 2026.11 classes.

Run with a Home Assistant Core 2026.11 install (the dev branch today, 2026.11.0b0 once
it is out):  python check.py

Each line runs one operation copied from an integration listed in the README, or the
replacement Home Assistant documents. Integration code itself is not imported or run.
"""
import asyncio
import copy
import tempfile

from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import restore_state
from homeassistant.helpers.device_registry import DeviceInfo


def info():
    return DeviceInfo(identifiers={("demo", "1")}, name="Demo")


def run(label, fn):
    try:
        fn()
        print(f"ok      {label}")
    except Exception as exc:  # noqa: BLE001
        print(f"raises  {label}: {type(exc).__name__}: {exc}")


def vivint():  # camera.py: base entity set a DeviceInfo, camera adds a MAC connection
    info().setdefault("connections", set()).add(("mac", "aa:bb:cc:dd:ee:ff"))


def vivint_fixed():  # the base DeviceInfo sets no connections, so assign the set
    d = info()
    d["connections"] = {("mac", "aa:bb:cc:dd:ee:ff")}


def empty_is_falsy():  # eg4_web_monitor: an empty DeviceInfo() means "no parent link"
    if bool(DeviceInfo()):
        raise AssertionError("bool(DeviceInfo()) is True, so the link check passes")


def update_kwargs():  # flashbird: rename with keyword arguments
    info().update(name="Other")


def update_mapping():  # the form that still works
    info().update({"name": "Other"})


def copy_method():  # hasl3 sensors, hcu select: copy a DeviceInfo, then rename
    d = info().copy()
    d["name"] = "Other"


def copy_fixed():  # documented replacement
    d = copy.copy(info())
    d.name = "Other"


async def restore():
    with tempfile.TemporaryDirectory() as config_dir:
        hass = HomeAssistant(config_dir)
        dr.async_setup(hass)
        await dr.async_load(hass, load_empty=True)
        await er.async_load(hass, load_empty=True)
        data = restore_state.RestoreStateData(hass)
        run("last_states.get(entity_id)", lambda: data.last_states.get("sensor.demo"))
        run("last_states.items()", lambda: list(data.last_states.items()))
        run(
            "hasattr guard, then async_get_stored_state.get(entity_id, None)",
            lambda: data.async_get_stored_state.get("sensor.demo", None)
            if hasattr(data, "async_get_stored_state")
            else None,
        )
        run(
            "async_get_stored_state(entity_id)  [documented replacement]",
            lambda: data.async_get_stored_state("sensor.demo"),
        )
        await hass.async_stop(force=True)


def main():
    print(f"Home Assistant {__version__}")
    run("DeviceInfo.setdefault('connections', set()).add(...)", vivint)
    run("device_info['connections'] = {...}", vivint_fixed)
    run("DeviceInfo.copy(), then ['name'] =", copy_method)
    run("copy.copy(device_info), then .name =  [documented replacement]", copy_fixed)
    run("not DeviceInfo() as a 'no link' test", empty_is_falsy)
    run("DeviceInfo.update(name=...)", update_kwargs)
    run("DeviceInfo.update({'name': ...})", update_mapping)
    asyncio.run(restore())


if __name__ == "__main__":
    main()
