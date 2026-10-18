"""Check the Home Assistant 2026.11 "cannot import name" breaks and their one-line fixes.

Run with a Home Assistant Core install (the dev branch today, 2026.11.0b0 once it is out,
or 2026.10.x to confirm the fixes also work there):  python check.py

Each line imports one name the way an affected integration does, then imports it from the
replacement module. Only Home Assistant and its own dependencies are imported; no
integration code is imported or run.
"""
import inspect
import logging

logging.disable(logging.CRITICAL)  # camera import logs a missing optional libturbojpeg

from homeassistant.const import __version__

# (package the integrations import from, name, module that still provides it)
BREAKS = [
    ("homeassistant.components.script", "ATTR_LAST_TRIGGERED", "homeassistant.components.script.const"),
    ("homeassistant.components.event", "EventExtraStoredData", "homeassistant.components.event.entity"),
    ("homeassistant.components.text", "RestoreEntity", "homeassistant.helpers.restore_state"),
    ("homeassistant.components.sensor", "RestoreEntity", "homeassistant.helpers.restore_state"),
    ("homeassistant.components.input_boolean", "RestoreEntity", "homeassistant.helpers.restore_state"),
    ("homeassistant.components.sensor", "EntityCategory", "homeassistant.const"),
    ("homeassistant.components.sensor", "UnitOfTemperature", "homeassistant.const"),
    ("homeassistant.components.climate", "UnitOfTemperature", "homeassistant.const"),
    ("homeassistant.components.sensor", "CONF_UNIT_OF_MEASUREMENT", "homeassistant.const"),
    ("homeassistant.components.sensor", "StateType", "homeassistant.helpers.typing"),
    ("homeassistant.components.sensor", "HomeAssistantError", "homeassistant.exceptions"),
    ("homeassistant.components.sensor", "Entity", "homeassistant.helpers.entity"),
    ("homeassistant.components.persistent_notification", "async_dispatcher_send", "homeassistant.helpers.dispatcher"),
    ("homeassistant.components.time", "time", "datetime"),
    ("homeassistant.components.sensor", "datetime", "datetime"),
    ("homeassistant.components.sensor", "dataclass", "dataclasses"),
    ("homeassistant.components.sensor", "cached_property", "propcache.api"),
    ("homeassistant.components.camera", "RTCIceCandidateInit", "webrtc_models"),
    ("homeassistant.components.wake_on_lan", "SERVICE_SEND_MAGIC_PACKET", "homeassistant.components.wake_on_lan.services"),
    ("homeassistant.components.zone", "DATA_ZONE_STORAGE_COLLECTION", None),
    ("homeassistant.helpers.entity_registry", "async_get_unprefixed_name", None),
    ("homeassistant.helpers.event", "async_track_state_change", "homeassistant.helpers.event"),
]
# 2026.11 only (2026.10 has no such module; keep the old import as an ImportError fallback):
#   event.entity, wake_on_lan.services
# The async_track_state_change replacement is a different function with a different callback:
REPLACEMENT_NAME = {"async_track_state_change": "async_track_state_change_event"}


def try_import(module, name):
    statement = f"from {module} import {name}"
    try:
        exec(statement, {})  # the same statement the integration runs
    except ModuleNotFoundError as exc:
        if exc.name and not module.startswith(exc.name):  # a dependency is missing, not the name
            return f"skip    {statement}: install {exc.name} to check this line"
        return f"raises  {statement}: {type(exc).__name__}: {exc}"
    except ImportError as exc:
        return f"raises  {statement}: {type(exc).__name__}: {str(exc).split(' (')[0]}"
    return f"ok      {statement}"


print("Home Assistant", __version__)
for module, name, fix in BREAKS:
    print(try_import(module, name))
    if fix:
        print("   fix  " + try_import(fix, REPLACEMENT_NAME.get(name, name)))

from homeassistant.components.auth import indieauth  # noqa: E402

params = inspect.signature(indieauth.verify_client_id).parameters
kwonly = [p for p, v in params.items() if v.kind is v.KEYWORD_ONLY and v.default is v.empty]
print(f"{'raises ' if kwonly else 'ok     '} indieauth.verify_client_id(client_id): required keyword-only {kwonly}")
