# Home Assistant 2026.11: what still breaks after the maintainers' outreach

Home Assistant Core 2026.11 removes `RestoreStateData.last_states` and turns `DeviceInfo`
into a dataclass. The beta is due around October 28 and the release around November 4.
Neither change has a deprecation period for the patterns below.

The core maintainers searched every repository in the HACS default list and contacted the
authors they found: one list of DeviceInfo misuses
([core#185211](https://github.com/home-assistant/core/issues/185211), October 9) and one
issue per affected repository for `last_states` (October 6). We repeated the search on
October 18 over 3,219 of the 3,241 repositories in that list, read every hit by hand, and
replayed each failing operation on the real 2026.11 classes. A second scan, built
separately from the same written method, then repeated the search. Each scan found breaks
the other missed, so the list below is a floor, not a complete count. Together they found
three groups that the outreach has not closed:

- **At least 10 integrations contain affected code paths outside the two public outreach
  sets we checked.** Some paths are conditional or affect initial restoration rather than
  permanent stored data.
- **1 closed issue whose fix still fails.** FordPass shipped a guard that raises on 2026.11.
- **5 notified integrations still unfixed** at HEAD, including pyscript, which fails setup.

If you maintain a custom integration, the fixes are in the two migration posts:
[`last_states` removal](https://contributors.home-assistant.io/blog/2026/10/06/restore-state-last-states-removal/)
and [DeviceInfo is now a dataclass](https://contributors.home-assistant.io/blog/2026/10/13/device-info-class/).
If you use one of the integrations below, check for an update before you install 2026.11.

## Not covered by the public outreach checked

| integration | what fails on 2026.11 | opt-in installs | code (Oct 18) |
|---|---|---:|---|
| [BenPru/luxtronik](https://github.com/BenPru/luxtronik) | reads `last_states`; setup fails with the EVU2 manual model and its switch enabled | 666 | [`custom_components/luxtronik2/coordinator.py:338`](https://github.com/BenPru/luxtronik/blob/5887859e7e431e1e29c4cc38a40aee52b9abf867/custom_components/luxtronik2/coordinator.py#L338) |
| [natekspencer/ha-vivint](https://github.com/natekspencer/ha-vivint) | `.setdefault()` on a `DeviceInfo`; camera entities fail | 489 | [`custom_components/vivint/camera.py:109`](https://github.com/natekspencer/ha-vivint/blob/b0d8b4e6db817b7023d5abe6cc10f13f51c9e570/custom_components/vivint/camera.py#L109) |
| [EiS94/db_info](https://github.com/EiS94/db_info) | reads `last_states` inside a broad `except`; the coordinator cannot seed stored time settings before its first refresh. The switch and datetime entities have their own later restore paths. | 345 | [`custom_components/db_info/coordinator.py:74`](https://github.com/EiS94/db_info/blob/2cfcb01e92f93e33e156e25dda8a639c679d7276/custom_components/db_info/coordinator.py#L74) |
| [Ediminator/homematicip-hcu](https://github.com/Ediminator/homematicip-hcu) | `.copy()` on a `DeviceInfo`; fails for renamed alarm-switching groups (default branch, not release 2.3.0) | 338 | [`custom_components/hcu_integration/select.py:128`](https://github.com/Ediminator/homematicip-hcu/blob/ff9f9e09c4b4e74f117563d5563e6d9940b99137/custom_components/hcu_integration/select.py#L128) |
| [joyfulhouse/eg4_web_monitor](https://github.com/joyfulhouse/eg4_web_monitor) | an empty `DeviceInfo()` is now truthy; if the parent is not registered, unlinked device info is cached for the current update cycle. Later device-registry re-linking was not tested. | 270 | [`custom_components/eg4_web_monitor/coordinator_mixins.py:4212`](https://github.com/joyfulhouse/eg4_web_monitor/blob/713b44651be77df8f2426409ba5ca5e74a7c3d2a/custom_components/eg4_web_monitor/coordinator_mixins.py#L4212) |
| [hasl-sensor/integration](https://github.com/hasl-sensor/integration) | `.copy()` on a module `DeviceInfo` constant, called while the integration sets up; setup fails, so no sensors load | 160 | [`custom_components/hasl3/sensors/departure.py:135`](https://github.com/hasl-sensor/integration/blob/87b88276490c7a5abab7f092fdffd515a04c4c4b/custom_components/hasl3/sensors/departure.py#L135) |
| [gorfo66/flashbird-homeassistant](https://github.com/gorfo66/flashbird-homeassistant) | `.update(name=...)` on a `DeviceInfo` raises `TypeError`, so device info for the lock, tracker and sensors fails. The migration post says `.update()` still works; that holds for `.update({...})`, not for keyword arguments. | 10 | [`custom_components/flashbird/helpers/device_info.py:28`](https://github.com/gorfo66/flashbird-homeassistant/blob/6244ac3b24da57c4017073cf900c723ad2cc625b/custom_components/flashbird/helpers/device_info.py#L28) |
| [jharris4/molight](https://github.com/jharris4/molight) | reads `last_states`; fails when an entity is renamed | not reported | [`custom_components/molight/helpers.py:170`](https://github.com/jharris4/molight/blob/14740919a3ddf817be30e624d43c552941580889/custom_components/molight/helpers.py#L170) |
| [jyourstone/energy_manager](https://github.com/jyourstone/energy_manager) | reads `last_states` inside an `except`; coordinator values fall back to defaults during initialization. `RestoreNumber` entities can restore them later. | not reported | [`custom_components/energy_manager/coordinator.py:600`](https://github.com/jyourstone/energy_manager/blob/6a9c7b016f5b1fd331bde3fde3ba6f55d0050c99/custom_components/energy_manager/coordinator.py#L600) |
| [traktore-org/sem-community](https://github.com/traktore-org/sem-community) | the restore-store fallback reads `last_states` inside an `except`; if the flag is absent from `entry.options` and `entry.data`, that fallback returns no restored flag | not reported | [`persisted_flags.py:86`](https://github.com/traktore-org/sem-community/blob/d2becbcdc102a46b8a3ebfaa9a7a9c5560ee75df/persisted_flags.py#L86) |

The seven domains reported in the opt-in analytics total 2,278 installations across all
versions; three domains were not reported. These are not counts of affected installations.

## Notified, still affected

| integration | status | opt-in installs |
|---|---|---:|
| [custom-components/pyscript](https://github.com/custom-components/pyscript) | `async_setup` iterates `last_states`, so the integration does not load. Issue #877 open since October 6; release 2.1.0 and HEAD unchanged. | 7,876 |
| [Zendure/Zendure-HA](https://github.com/Zendure/Zendure-HA) | a one-time entity migration reads `last_states`; it fails with a logged error and renamed entities are not migrated. Issue #1694 open | 4,204 |
| [marq24/ha-fordpass](https://github.com/marq24/ha-fordpass) | issue #275 closed by release 2026.10.2, whose guard still raises (below) | 1,990 |
| [steamEngineer/bravia-quad-homeassistant](https://github.com/steamEngineer/bravia-quad-homeassistant) | select and switch restore helpers raise; issue #236 open | 81 |
| [pajeronda/xai_conversation](https://github.com/pajeronda/xai_conversation) | raises when its entities are removed; issue #26 open | 51 |
| [alepee/hass-hitachi_yutaki](https://github.com/alepee/hass-hitachi_yutaki) | setup fails once its energy sensors exist; issue #458 open, fix PR #469 open | 21 |

## A guard written on 2026.10 cannot test the 2026.11 branch

FordPass supports both versions with a `hasattr` check (`custom_components/fordpass/sensor.py:70-73`
in release 2026.10.2):

```python
if hasattr(storage, "async_get_stored_state"):
    restored_state = storage.async_get_stored_state.get(entity_id, None)
elif hasattr(storage, "last_states"):
    restored_state = storage.last_states.get(entity_id, None)
```

On 2026.10 the first branch never runs, so the code works. On 2026.11 it runs and calls
`.get` on a method: `AttributeError: 'function' object has no attribute 'get'`, raised in
the sensor platform's setup outside its `try`. The fix is one call:
`storage.async_get_stored_state(entity_id)`. If you add a guard like this, run it once
against the 2026.11 beta.

## Check it yourself

[`check.py`](check.py) replays each failing operation and each documented replacement on
the installed Home Assistant classes. It does not import or run any integration.

```sh
python check.py
```

Output on `2026.11.0.dev0` (core `dev` at 1b740dcd, Python 3.14.3). `raises` means the integration's code fails; `ok` means the replacement works:

```text
Home Assistant 2026.11.0.dev0
raises  DeviceInfo.setdefault('connections', set()).add(...): AttributeError: 'DeviceInfo' object has no attribute 'setdefault'
ok      device_info['connections'] = {...}
raises  DeviceInfo.copy(), then ['name'] =: AttributeError: 'DeviceInfo' object has no attribute 'copy'
ok      copy.copy(device_info), then .name =  [documented replacement]
raises  not DeviceInfo() as a 'no link' test: AssertionError: bool(DeviceInfo()) is True, so the link check passes
raises  DeviceInfo.update(name=...): TypeError: _DeviceInfoMapping.update() got an unexpected keyword argument 'name'
ok      DeviceInfo.update({'name': ...})
raises  last_states.get(entity_id): AttributeError: 'RestoreStateData' object has no attribute 'last_states'
raises  last_states.items(): AttributeError: 'RestoreStateData' object has no attribute 'last_states'
raises  hasattr guard, then async_get_stored_state.get(entity_id, None): AttributeError: 'function' object has no attribute 'get'
ok      async_get_stored_state(entity_id)  [documented replacement]
```

## Method and limits

- Frame: `hacs/default` `integration` list at commit 2e08a24e (3,241 repositories). 3,219
  were cloned at HEAD on October 18; 22 failed to clone twice and were not read.
- A static scan found DeviceInfo and `last_states` candidates; every candidate in a
  repository not already covered by the outreach was read by hand. Two were dismissed after
  reading.
- A second scanner, written separately from the same method description, repeated the scan
  and adjudication without the complete first hit list, although earlier context exposed the
  first count and two named findings; the second pass was not fully blind. It matched 13 of the first scan's 14
  confirmed rows and both dismissals, and found eg4_web_monitor and flashbird, which the
  first scan missed. It missed hasl-sensor, which uses a `DeviceInfo` constant imported from
  another module. Breaks hidden behind cross-module or dynamic code are likely still missed.
  Both scans ran on the same machine and were made by the same team, so this is a second
  execution, not an independent reproduction.
- Severity comes from reading each call path. The integrations were not run.
- Core is the `dev` branch, not a release. The beta could still add a compatibility shim.
- Repositories outside the HACS default list are not covered, as in the maintainers' scan.
- Installs are the `total` for each domain in Home Assistant's opt-in analytics
  (`analytics.home-assistant.io/custom_integrations.json`, October 18). These are opt-in
  reporting totals across versions, not a census of all installs.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
