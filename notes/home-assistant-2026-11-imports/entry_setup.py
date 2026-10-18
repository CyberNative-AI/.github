"""Show what one broken platform import does to an integration's setup.

Run with a Home Assistant Core install:  python entry_setup.py

Each case writes a throwaway integration into a temporary config directory. It has a
healthy sensor platform and a second platform whose only difference between cases is one
import line: ATTR_LAST_TRIGGERED from homeassistant.components.script (the removed path)
or from homeassistant.components.script.const (the fix). No real integration is imported
or run.
"""
import asyncio
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

from homeassistant import bootstrap, config_entries, core, loader
from homeassistant.const import __version__
from homeassistant.setup import async_setup_component


class OneLine(logging.Formatter):
    def format(self, record):  # first line of the message, then the exception, no traceback
        text = f"  log  {record.levelname} {record.name}: {record.getMessage().splitlines()[0]}"
        exc = record.exc_info[1] if record.exc_info else None
        if exc is None and record.name == "asyncio":
            exc = getattr(record, "exception", None)
        if exc is not None:
            text += f"\n  log  {type(exc).__name__}: {str(exc).split(' (')[0]}"
        return text


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(OneLine())
logging.basicConfig(level=logging.ERROR, handlers=[handler])
logging.getLogger("homeassistant.components.camera").setLevel(logging.CRITICAL)

REMOVED = "from homeassistant.components.script import ATTR_LAST_TRIGGERED"
FIXED = "from homeassistant.components.script.const import ATTR_LAST_TRIGGERED"
MANIFEST = json.dumps({"domain": "demoint", "name": "Demo", "version": "0.0.1",
                       "config_flow": True, "documentation": "https://example.invalid",
                       "codeowners": [], "iot_class": "local_polling", "requirements": []})
FLOW = ("from homeassistant import config_entries\n"
        "class Flow(config_entries.ConfigFlow, domain='demoint'):\n    VERSION = 1\n")
FORWARD = {
    "awaited": "    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)\n",
    "add_job": "    hass.add_job(hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))\n",
}
ENTRY_SENSOR = ("from homeassistant.components.sensor import SensorEntity\n"
                "async def async_setup_entry(hass, entry, add):\n"
                "    e = SensorEntity(); e._attr_unique_id = 'demo_s'; e._attr_name = 'demo s'\n"
                "    add([e])\n")
ENTRY_BUTTON = ("from homeassistant.components.button import ButtonEntity\n{imp}\n"
                "async def async_setup_entry(hass, entry, add):\n    add([])\n")
YAML_SENSOR = ("from homeassistant.components.sensor import SensorEntity\n"
               "async def async_setup_platform(hass, config, add, discovery_info=None):\n"
               "    e = SensorEntity(); e._attr_name = 'demo s'\n    add([e])\n")
YAML_BINARY = ("from homeassistant.components.binary_sensor import BinarySensorEntity\n{imp}\n"
               "async def async_setup_platform(hass, config, add, discovery_info=None):\n"
               "    e = BinarySensorEntity(); e._attr_name = 'demo b'\n    add([e])\n")

CASES = {
    "awaited-removed": ("awaited", REMOVED),
    "awaited-fixed": ("awaited", FIXED),
    "add_job-removed": ("add_job", REMOVED),
    "yaml-removed": ("yaml", REMOVED),
}


async def run(shape, imp):
    with tempfile.TemporaryDirectory() as cfg:
        d = Path(cfg, "custom_components", "demoint")
        d.mkdir(parents=True)
        if shape == "yaml":
            files = {"manifest.json": MANIFEST, "__init__.py": "",
                     "sensor.py": YAML_SENSOR, "binary_sensor.py": YAML_BINARY.format(imp=imp)}
        else:
            files = {"manifest.json": MANIFEST, "config_flow.py": FLOW,
                     "__init__.py": "PLATFORMS = ['sensor', 'button']\n"
                                    "async def async_setup_entry(hass, entry):\n"
                                    + FORWARD[shape] + "    return True\n",
                     "sensor.py": ENTRY_SENSOR, "button.py": ENTRY_BUTTON.format(imp=imp)}
        for name, text in files.items():
            (d / name).write_text(text, encoding="utf-8")
        hass = core.HomeAssistant(cfg)
        hass.config.skip_pip = True
        loader.async_setup(hass)
        hass.config_entries = config_entries.ConfigEntries(hass, {})
        await bootstrap.async_load_base_functionality(hass)
        await async_setup_component(hass, "homeassistant", {})
        state = "(YAML, no entry)"
        if shape == "yaml":
            for domain in ("sensor", "binary_sensor"):
                await async_setup_component(hass, domain, {domain: [{"platform": "demoint"}]})
            await hass.async_block_till_done()
        else:
            entry = config_entries.ConfigEntry(
                domain="demoint", title="Demo", data={}, options={}, source="user", version=1,
                minor_version=1, unique_id=None, discovery_keys={}, subentries_data=None)
            await hass.config_entries.async_add(entry)
            await hass.async_block_till_done()
            state = entry.state.name
        entities = sorted(s.entity_id for s in hass.states.async_all()
                          if s.domain in ("sensor", "binary_sensor"))
        which = "removed import" if imp == REMOVED else "fixed import"
        print(f"{shape:<8} {which:<15} entry {state:<17} entities {entities}")
        await hass.async_stop(force=True)


if len(sys.argv) > 1:
    asyncio.run(run(*CASES[sys.argv[1]]))
else:
    print("Home Assistant", __version__, flush=True)
    for case in CASES:  # one process per case: Home Assistant caches loaded integrations
        subprocess.run([sys.executable, *sys.argv, case], check=True)
