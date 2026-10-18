# Home Assistant 2026.11: "cannot import name" errors in custom integrations, and compatible imports

In mid-October, Home Assistant Core moved each entity platform's classes into a separate
`entity.py` module and gave the platform packages an explicit `__all__` (for example
[#186863](https://github.com/home-assistant/core/pull/186863) for `sensor` and
[#186835](https://github.com/home-assistant/core/pull/186835) for `climate`). Some incidental
names that a package imported only for its own use moved out of the package root with that
refactor. They are no longer bound in the package, so an explicit import of them fails
(`__all__` alone would not stop it): `from homeassistant.components.sensor import StateType`
now raises `ImportError`.

The sensor pull request says the public classes are still exported, "so nothing changes for
integrations importing them". That is true for the classes it lists. The climate pull
request ([#186602](https://github.com/home-assistant/core/pull/186602)) notes that a few
custom integrations import `UnitOfTemperature` from `climate` and calls this "a bad
pattern". The changes are on the `dev` branch. They will ship in 2026.11, with the beta due
around October 28, unless core adds a compatibility shim. On October 18 it had none.

We checked every Home Assistant import in 3,219 of the 3,241 repositories in the HACS
default integration list. **47 integrations import a name removed by these refactors. In 45,
static reading predicts that at least one config-entry setup path fails on the checked
2026.11 dev build.** The 45 report 78,263 installations in Home Assistant's opt-in
analytics; SonoffLAN alone reports 45,671. Twelve more break on other 2026.11 changes,
listed further down.

For most removed imports below, the replacement is one import line. The event import needs
the compatibility fallback shown below, and we have not checked a replacement for
`DATA_ZONE_STORAGE_COLLECTION`. If you use one of these integrations, check for an update
before you install the 2026.11 beta.

## What you will see

Most integrations set up their platforms by awaiting `async_forward_entry_setups` in
`async_setup_entry`. If a platform in that call fails to import, the call raises and the
config entry ends in "Failed to set up". No platforms from that forwarding batch load. Other
entry types or separately loaded batches can behave differently.

[`entry_setup.py`](entry_setup.py) shows this with a throwaway integration. It has a working
sensor platform and a second platform that differs between runs by one import line. On
`2026.11.0.dev0` (core `dev` at b19ddb39, Python 3.14.3):

```text
Home Assistant 2026.11.0.dev0
  log  ERROR homeassistant.config_entries: Error setting up entry Demo for demoint
  log  ImportError: cannot import name 'ATTR_LAST_TRIGGERED' from 'homeassistant.components.script'
awaited  removed import  entry SETUP_ERROR       entities []
awaited  fixed import    entry LOADED            entities ['sensor.demo_s']
  log  ERROR asyncio: Task exception was never retrieved
  log  ImportError: cannot import name 'ATTR_LAST_TRIGGERED' from 'homeassistant.components.script'
add_job  removed import  entry LOADED            entities []
  log  ERROR homeassistant.config: platform_component_load_exc
  log  ImportError: cannot import name 'ATTR_LAST_TRIGGERED' from 'homeassistant.components.script'
yaml     removed import  entry (YAML, no entry)  entities ['sensor.demo_s']
```

On 2026.10.2, all four runs load the sensor, and the YAML run also loads the binary sensor.

- **Awaited forward** (most integrations): the config entry fails to set up and no entities
  from that forwarding batch load.
- **Forward scheduled with `hass.add_job`**: the integration shows as loaded but has no
  entities. The only trace in the log is "Task exception was never retrieved".
- **YAML platform** (`platform:` under a domain in `configuration.yaml`): only the platform
  with the broken import is lost.

## The fixes

| `from homeassistant.components.…` | name | import it from | also works on 2026.10 |
|---|---|---|---|
| `script` | `ATTR_LAST_TRIGGERED` | `homeassistant.components.script.const` | yes |
| `sensor`, `text`, `input_boolean` | `RestoreEntity` | `homeassistant.helpers.restore_state` | yes |
| `sensor`, `climate` | `UnitOfTemperature` | `homeassistant.const` | yes |
| `sensor` | `EntityCategory`, `CONF_UNIT_OF_MEASUREMENT` | `homeassistant.const` | yes |
| `sensor` | `StateType` | `homeassistant.helpers.typing` | yes |
| `sensor` | `HomeAssistantError` | `homeassistant.exceptions` | yes |
| `sensor` | `Entity` | `homeassistant.helpers.entity` | yes |
| `persistent_notification` | `async_dispatcher_send` | `homeassistant.helpers.dispatcher` | yes |
| `time`, `sensor` | `time`, `datetime` | `datetime` (standard library) | yes |
| `sensor` | `dataclass` | `dataclasses` (standard library) | yes |
| `sensor` | `cached_property` | `propcache.api` | yes |
| `camera` | `RTCIceCandidateInit` | `webrtc_models` | yes |
| `event` | `EventExtraStoredData` | `homeassistant.components.event.entity` | no, see below |
| `wake_on_lan` | `SERVICE_SEND_MAGIC_PACKET` | `homeassistant.components.wake_on_lan.services` | no, see below |
| `zone` | `DATA_ZONE_STORAGE_COLLECTION` | removed; no replacement checked | |

`event.entity` and `wake_on_lan.services` do not exist in 2026.10. To support both versions,
keep the old import as a fallback:

```python
try:
    from homeassistant.components.event.entity import EventExtraStoredData
except ImportError:  # Home Assistant 2026.10 and earlier
    from homeassistant.components.event import EventExtraStoredData
```

The `wake_on_lan` constant is the service name `"send_magic_packet"` in both versions.

## Integrations that import a removed name

Read at each repository's default branch HEAD on October 18; every cited line was re-read
at the linked commit. Installs are opt-in analytics totals, not counts of affected
installations.

Effects below are predictions for the affected setup paths, based on static source reading
and the synthetic tests, rather than executions of these integrations. For example,
OctopusEnergy's account and tariff-comparison entries forward the broken event platform; its
cost-tracker entry forwards only sensor.

[We found an issue about this change in niko-home-control-II](https://github.com/joleys/niko-home-control-II/issues/321),
opened by a core maintainer on October 14. In the results we inspected for the other
repositories, we found no further issue or pull request about these re-export removals.
These were bounded keyword searches, not an exhaustive check: the home-connect-hass query
returned 155 results, of which only the first 30 were retained, and the ha-unifi-insights
query did not complete.

| integration | opt-in installs | removed import (code at HEAD, October 18) | predicted effect on checked 2026.11 dev |
|---|---:|---|---|
| [AlexxIT/SonoffLAN](https://github.com/AlexxIT/SonoffLAN) | 45,671 | `ATTR_LAST_TRIGGERED` from `components.script`: [`binary_sensor.py:7`](https://github.com/AlexxIT/SonoffLAN/blob/08135f0bef69a46edbe19b86c6b6c548cc570e85/custom_components/sonoff/binary_sensor.py#L7) (+1 file) | affected entry fails setup |
| [BottlecapDave/HomeAssistant-OctopusEnergy](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy) | 10,410 | `EventExtraStoredData` from `components.event`: [`rates_current_day.py:7`](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy/blob/fb6c839f740d2d3c641737602757e8bc160ce12a/custom_components/octopus_energy/electricity/rates_current_day.py#L7) (+1 file) | affected entry fails setup |
| [AlexandrErohin/home-assistant-flightradar24](https://github.com/AlexandrErohin/home-assistant-flightradar24) | 6,589 | `RestoreEntity` from `components.text`: [`text.py:12`](https://github.com/AlexandrErohin/home-assistant-flightradar24/blob/8cffeb79b6b0d430dcc7741d39238f80130a4b7a/custom_components/flightradar24/text.py#L12) | affected entry fails setup |
| [ekutner/home-connect-hass](https://github.com/ekutner/home-connect-hass) | 3,934 | `time` from `components.time`: [`time.py:4`](https://github.com/ekutner/home-connect-hass/blob/f74cffd95724802d723fc62e5da719da82ab6f0a/custom_components/home_connect_alt/time.py#L4) | affected entry fails setup |
| [AlexxIT/XiaomiGateway3](https://github.com/AlexxIT/XiaomiGateway3) | 3,233 | `ATTR_LAST_TRIGGERED` from `components.script`: [`binary_sensor.py:7`](https://github.com/AlexxIT/XiaomiGateway3/blob/65f7249901803b40ef0c58e717754f5220c9f273/custom_components/xiaomi_gateway3/binary_sensor.py#L7) | affected entry fails setup |
| [bjrnptrsn/climate_group_helper](https://github.com/bjrnptrsn/climate_group_helper) | 1,500 | `EntityCategory` from `components.sensor`: [`sensor.py:14`](https://github.com/bjrnptrsn/climate_group_helper/blob/9e59b0211d2750f0243b135fb7c6faaba61d80fe/custom_components/climate_group_helper/sensor.py#L14) | affected entry fails setup |
| [jjjonesjr33/petlibro](https://github.com/jjjonesjr33/petlibro) | 1,396 | `dataclass` from `components.sensor`: [`entity.py:34`](https://github.com/jjjonesjr33/petlibro/blob/7ee757fa8f76f628af2e845a301335656e9919a1/custom_components/petlibro/pets/entity.py#L34) | affected entry fails setup |
| [pyalarmdotcom/alarmdotcom](https://github.com/pyalarmdotcom/alarmdotcom) | 917 | `UnitOfTemperature` from `components.climate`: [`climate.py:18`](https://github.com/pyalarmdotcom/alarmdotcom/blob/0eefd0b76a98be0a229be07f64f71c0840b771c5/custom_components/alarmdotcom/climate.py#L18) | affected entry fails setup |
| [thecem/octopus_germany](https://github.com/thecem/octopus_germany) | 854 | `RestoreEntity` from `components.sensor`: [`charging.py:11`](https://github.com/thecem/octopus_germany/blob/adff6c388fb12f59775eb6c04f519086e15a5f06/custom_components/octopus_germany/entities/charging.py#L11) | affected entry fails setup |
| [dan-r/HomeAssistant-NissanConnect](https://github.com/dan-r/HomeAssistant-NissanConnect) | 638 | `UnitOfTemperature` from `components.sensor`: [`sensor.py:7`](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b575cd136f757585e1ad58b927b05a11b4085a74/custom_components/nissan_connect/sensor.py#L7) | affected entry fails setup |

<details><summary>The other 37</summary>

| integration | opt-in installs | removed import (code at HEAD, October 18) | predicted effect on checked 2026.11 dev |
|---|---:|---|---|
| [gjohansson-ST/attribute_as_sensor](https://github.com/gjohansson-ST/attribute_as_sensor) | 585 | `CONF_UNIT_OF_MEASUREMENT` from `components.sensor`: [`config_flow.py:11`](https://github.com/gjohansson-ST/attribute_as_sensor/blob/10795bb11c5fa2abe27917171d0581dccf51c990/custom_components/attribute_as_sensor/config_flow.py#L11) | affected entry fails setup |
| [custom-components/weatheralerts](https://github.com/custom-components/weatheralerts) | 576 | `RestoreEntity` from `components.sensor`: [`sensor.py:11`](https://github.com/custom-components/weatheralerts/blob/7c01f7f498d0676db71cf8f665076c5a2aeb63c2/custom_components/weatheralerts/sensor.py#L11) | affected entry fails setup |
| [joleys/niko-home-control-II](https://github.com/joleys/niko-home-control-II) | 539 | `RestoreEntity` from `components.input_boolean`: [`nhc_entity.py:1`](https://github.com/joleys/niko-home-control-II/blob/b0b26282f9946e3b3c3074a750504fb871b16900/custom_components/nhc2/entities/nhc_entity.py#L1) | shows loaded, no entities (a core maintainer opened an issue Oct 14) |
| [ruaan-deysel/ha-unifi-insights](https://github.com/ruaan-deysel/ha-unifi-insights) | 393 | `EntityCategory` from `components.sensor`: [`sensor.py:12`](https://github.com/ruaan-deysel/ha-unifi-insights/blob/5c09c5a75fae41fe843e1f410f0d55d346fabcdd/custom_components/unifi_insights/sensor.py#L12) | affected entry fails setup |
| [joggs/home_assistant_ebeco](https://github.com/joggs/home_assistant_ebeco) | 305 | `StateType` from `components.sensor`: [`sensor.py:11`](https://github.com/joggs/home_assistant_ebeco/blob/1c6d5b7348340887e6da879d44b1ff8b202f2773/custom_components/ebeco/sensor.py#L11) | affected entry fails setup |
| [MiguelAngelLV/ha-balance-neto](https://github.com/MiguelAngelLV/ha-balance-neto) | 259 | `RestoreEntity` from `components.sensor`: [`sensor.py:13`](https://github.com/MiguelAngelLV/ha-balance-neto/blob/29ad412618a762f4c4ca2e6bbc2a2a290528de8d/custom_components/balance_neto/sensor.py#L13) | affected entry fails setup |
| [MiguelAngelLV/ha-tarifa-20td](https://github.com/MiguelAngelLV/ha-tarifa-20td) | 248 | `RestoreEntity` from `components.sensor`: [`sensor.py:13`](https://github.com/MiguelAngelLV/ha-tarifa-20td/blob/2f18000083ff9691990c6453cf9177a707f1e4b2/custom_components/tarifa_20td/sensor.py#L13) | affected entry fails setup |
| [Tvalley71/pluggit](https://github.com/Tvalley71/pluggit) | 166 | `HomeAssistantError` from `components.sensor`: [`text.py:6`](https://github.com/Tvalley71/pluggit/blob/c6894e2bc798a76c3bff47cc74a17fa9e56877e5/custom_components/pluggit/text.py#L6) | affected entry fails setup |
| [Tvalley71/dantherm](https://github.com/Tvalley71/dantherm) | 89 | `HomeAssistantError` from `components.sensor`: [`text.py:6`](https://github.com/Tvalley71/dantherm/blob/a04c381a665248ea7da8dd568da22a28affc5dea/custom_components/dantherm/text.py#L6) | affected entry fails setup |
| [toringer/home-assistant-heru](https://github.com/toringer/home-assistant-heru) | 81 | `EntityCategory` from `components.sensor`: [`HeruQualitySensor.py:4`](https://github.com/toringer/home-assistant-heru/blob/ec1294fcd29f9495a95271c78a936514c3b1c806/custom_components/heru/HeruQualitySensor.py#L4) (+1 file) | affected entry fails setup |
| [golles/ha-tomtom-travel-time](https://github.com/golles/ha-tomtom-travel-time) | 72 | `StateType` from `components.sensor`: [`sensor.py:7`](https://github.com/golles/ha-tomtom-travel-time/blob/dfc5c24c048fb64b9eea8fff8f9f7d0127d216ba/custom_components/tomtom_travel_time/sensor.py#L7) | affected entry fails setup |
| [pyrech/homewizard_cloud_watermeter](https://github.com/pyrech/homewizard_cloud_watermeter) | 62 | `EntityCategory` from `components.sensor`: [`sensor.py:3`](https://github.com/pyrech/homewizard_cloud_watermeter/blob/48008d6036427e6281b10c43ddb9c435e7369b46/custom_components/homewizard_cloud_watermeter/sensor.py#L3) | affected entry fails setup |
| [thomasgriebner/retention_cleaner](https://github.com/thomasgriebner/retention_cleaner) | 55 | `EntityCategory` from `components.sensor`: [`sensor.py:6`](https://github.com/thomasgriebner/retention_cleaner/blob/b7d6a026ddddc261149ddfd1e6074a9b11b552dc/custom_components/retention_cleaner/sensor.py#L6) | affected entry fails setup |
| [MiguelAngelLV/ha-input-stats](https://github.com/MiguelAngelLV/ha-input-stats) | 53 | `RestoreEntity` from `components.sensor`: [`sensor.py:12`](https://github.com/MiguelAngelLV/ha-input-stats/blob/685a6e0382bc44932940e111cabe9938e20786cb/custom_components/input_stats/sensor.py#L12) | affected entry fails setup |
| [gicamm/homeassistant-comelit](https://github.com/gicamm/homeassistant-comelit) | 50 | `UnitOfTemperature` from `components.sensor`: [`climate.py:10`](https://github.com/gicamm/homeassistant-comelit/blob/13862470230b0080fcb076d756d86d19ac2f98f9/custom_components/comelit/climate.py#L10) | that YAML platform fails |
| [hexCut/irsap-ha](https://github.com/hexCut/irsap-ha) | 35 | `datetime` from `components.sensor`: [`sensor.py:7`](https://github.com/hexCut/irsap-ha/blob/4833bd0751ec0c29e241793fe813f864ca2766c0/custom_components/irsap_ha/sensor.py#L7) | affected entry fails setup |
| [3ll3d00d/jriver_homeassistant](https://github.com/3ll3d00d/jriver_homeassistant) | 22 | `SERVICE_SEND_MAGIC_PACKET` from `components.wake_on_lan`: [`__init__.py:19`](https://github.com/3ll3d00d/jriver_homeassistant/blob/2e5dbce8f0d7b5bc0fd97c32adfe36eae45519a3/custom_components/jriver/__init__.py#L19) | affected entry fails setup |
| [aceindy/Duepi_EVO](https://github.com/aceindy/Duepi_EVO) | 20 | `UnitOfTemperature` from `components.climate`: [`climate.py:17`](https://github.com/aceindy/Duepi_EVO/blob/950f9348396462c21fddd77e1844a50e56710ff8/custom_components/duepi_evo/climate.py#L17) | affected entry fails setup |
| [kgn3400/state_updated](https://github.com/kgn3400/state_updated) | 15 | `Entity` from `components.sensor`: [`component_api.py:6`](https://github.com/kgn3400/state_updated/blob/a138a7428a4bc2fdd6cbe2bb7282457ccb7e7fe2/custom_components/state_updated/component_api.py#L6) | affected entry fails setup |
| [iPeel/HA-Eleven-Energy](https://github.com/iPeel/HA-Eleven-Energy) | 13 | `EntityCategory` from `components.sensor`: [`hybrid_inverter.py:10`](https://github.com/iPeel/HA-Eleven-Energy/blob/2aea07022b11264ebae5c0b7db3e009ad981bebf/custom_components/eleven_energy/hybrid_inverter.py#L10) | affected entry fails setup |
| [Nazze/ha_best_bottrop_garbage_collection](https://github.com/Nazze/ha_best_bottrop_garbage_collection) | 12 | `RestoreEntity` from `components.sensor`: [`sensor.py:13`](https://github.com/Nazze/ha_best_bottrop_garbage_collection/blob/1c0d327975bb50d4ae47b91a89c0ccd9b385fe49/custom_components/best_bottrop_garbage_collection/sensor.py#L13) | affected entry fails setup |
| [golles/ha-aquatlantis-ori](https://github.com/golles/ha-aquatlantis-ori) | 11 | `StateType` from `components.sensor`: [`sensor.py:9`](https://github.com/golles/ha-aquatlantis-ori/blob/b9d31a412d657fd37d00677a069a59eb3a6cd3bb/custom_components/ori/sensor.py#L9) | affected entry fails setup |
| [iluvdata/pdf_scrape](https://github.com/iluvdata/pdf_scrape) | 11 | `cached_property` from `components.sensor`: [`sensor.py:9`](https://github.com/iluvdata/pdf_scrape/blob/be2095af8b7de172085f8411e9c7304329dad709/custom_components/pdf_scrape/sensor.py#L9) | affected entry fails setup |
| [martinstafford/daikin_d3net](https://github.com/martinstafford/daikin_d3net) | 8 | `UnitOfTemperature` from `components.climate`; `UnitOfTemperature` from `components.sensor`: [`climate.py:14`](https://github.com/martinstafford/daikin_d3net/blob/92ae9ab46c6ce6d737f1bfb7af6fd128983cbe2a/custom_components/daikin_d3net/climate.py#L14) (+2 files) | affected entry fails setup |
| [BottlecapDave/HomeAssistant-HarvestTimeTracker](https://github.com/BottlecapDave/HomeAssistant-HarvestTimeTracker) | 7 | `EventExtraStoredData` from `components.event`: [`tasks.py:8`](https://github.com/BottlecapDave/HomeAssistant-HarvestTimeTracker/blob/a7723ade8dea8d8f4a40a778b202b4cb60f0c7c3/custom_components/harvest_time_tracker/sensors/tasks.py#L8) | affected entry fails setup |
| [gjohansson-ST/response_as_sensor](https://github.com/gjohansson-ST/response_as_sensor) | 7 | `CONF_UNIT_OF_MEASUREMENT` from `components.sensor`: [`config_flow.py:12`](https://github.com/gjohansson-ST/response_as_sensor/blob/e67a2c89f2ef4747001acfd1cbe8fab86f529c7f/custom_components/response_as_sensor/config_flow.py#L12) | affected entry fails setup |
| [cleveroom-code/ha-cleveroom-home](https://github.com/cleveroom-code/ha-cleveroom-home) | 6 | `UnitOfTemperature` from `components.sensor`: [`sensor.py:12`](https://github.com/cleveroom-code/ha-cleveroom-home/blob/5fa4f7c5b17ecc8da8c5d2f85b994ed7c1dbae41/custom_components/cleveroom/sensor.py#L12) | affected entry fails setup |
| [tom42530/asys_ble_ha](https://github.com/tom42530/asys_ble_ha) | 6 | `RestoreEntity` from `components.sensor`: [`sensor.py:8`](https://github.com/tom42530/asys_ble_ha/blob/1ce64d06aeac5dbf0d9447b91df0665e9145f94d/custom_components/asys_ble/sensor.py#L8) | affected entry fails setup |
| [Beormund/tascam-bdmp4k](https://github.com/Beormund/tascam-bdmp4k) | 2 | `StateType` from `components.sensor`: [`sensor.py:5`](https://github.com/Beormund/tascam-bdmp4k/blob/2fa1ea34604b57d34f0914c30a5bc55cde4cbd2c/custom_components/tascam_bdmp4k/sensor.py#L5) | affected entry fails setup |
| [dneprojects/habitron](https://github.com/dneprojects/habitron) | 2 | `RTCIceCandidateInit` from `components.camera`: [`handlers.py:18`](https://github.com/dneprojects/habitron/blob/8c56c943dd9c8ddc5fc58d98872c226ce14c8e42/custom_components/habitron/ws_provider/handlers.py#L18) (+1 file) | affected entry fails setup |
| [Bobby5291/HomeAssistant-EDF-UK](https://github.com/Bobby5291/HomeAssistant-EDF-UK) | not reported | `EventExtraStoredData` from `components.event`: [`rates_events.py:7`](https://github.com/Bobby5291/HomeAssistant-EDF-UK/blob/ff45e757a3949ab7420a46f98df61ebaba391a8b/custom_components/edf_energy/electricity/rates_events.py#L7) | affected entry fails setup |
| [Jarauvi/elisa_kotiakku](https://github.com/Jarauvi/elisa_kotiakku) | not reported | `RestoreEntity` from `components.sensor`: [`sensor.py:8`](https://github.com/Jarauvi/elisa_kotiakku/blob/a4f5c77ec1472a6a69ac93c8e3620f92590c8377/custom_components/elisa_kotiakku/sensor.py#L8) | affected entry fails setup |
| [Veldkornet/ha-hyxi-cloud](https://github.com/Veldkornet/ha-hyxi-cloud) | not reported | `EntityCategory` from `components.sensor`: [`sensor.py:14`](https://github.com/Veldkornet/ha-hyxi-cloud/blob/318671a6343083db880eaf74e615f183bb3d3edc/custom_components/hyxi_cloud/sensor.py#L14) | affected entry fails setup |
| [bwcon/homeassistant-crestron-home](https://github.com/bwcon/homeassistant-crestron-home) | not reported | `UnitOfTemperature` from `components.climate`: [`climate.py:8`](https://github.com/bwcon/homeassistant-crestron-home/blob/e603e94d284a524a6ec63bd165374fc57946eb5c/custom_components/crestron_home/climate.py#L8) | affected entry fails setup |
| [lmt-lv/lmt-iot-ha-integration](https://github.com/lmt-lv/lmt-iot-ha-integration) | not reported | `RestoreEntity` from `components.sensor`: [`sensor.py:7`](https://github.com/lmt-lv/lmt-iot-ha-integration/blob/73f4b2a4c5f36d8271ce8164c3365c9e7068748e/custom_components/lmt_iot/sensor.py#L7) | affected entry fails setup |
| [swansmart/hivi_speaker](https://github.com/swansmart/hivi_speaker) | not reported | `async_dispatcher_send` from `components.persistent_notification`: [`discovery_scheduler.py:11`](https://github.com/swansmart/hivi_speaker/blob/00b34595882b7957c2aa89ec5b50b2bb14dfb8e7/custom_components/hivi_speaker/discovery_scheduler.py#L11) | affected entry fails setup |
| [tailgatelabs/ha-rutos-integration](https://github.com/tailgatelabs/ha-rutos-integration) | not reported | `DATA_ZONE_STORAGE_COLLECTION` from `components.zone`: [`__init__.py:9`](https://github.com/tailgatelabs/ha-rutos-integration/blob/79b9f9fcf1295cc3371e31c9d57d610d4d14da36/custom_components/rutos/__init__.py#L9) | affected entry fails setup |

</details>

## Other 2026.11 changes in the same scan

**`async_track_state_change` is removed**
([#184756](https://github.com/home-assistant/core/pull/184756), merged October 12). It was
[deprecated in April 2024](https://contributors.home-assistant.io/blog/2024/04/13/deprecate_async_track_state_change/)
for removal in 2025.5, and 2026.10 still logs a warning when it is called. The replacement,
`async_track_state_change_event`, passes the callback one `Event` instead of
`(entity_id, old_state, new_state)`, so the callback needs a small rewrite, not only a new
import. Ten integrations in the list still import it:

| integration | opt-in installs | removed import (code at HEAD, October 18) | predicted effect on checked 2026.11 dev |
|---|---:|---|---|
| [snarky-snark/home-assistant-variables](https://github.com/snarky-snark/home-assistant-variables) | 932 | `async_track_state_change` from `helpers.event`: [`__init__.py:24`](https://github.com/snarky-snark/home-assistant-variables/blob/040058b53fc790c5f6a21cd2855958b02b83753b/custom_components/var/__init__.py#L24) | affected entry fails setup |
| [jonasbkarlsson/ev_smart_charging](https://github.com/jonasbkarlsson/ev_smart_charging) | 623 | `async_track_state_change` from `helpers.event`: [`coordinator.py:37`](https://github.com/jonasbkarlsson/ev_smart_charging/blob/cb6cc76972ecf3e7098f26d273a9ebade9c7f062/custom_components/ev_smart_charging/coordinator.py#L37) | affected entry fails setup |
| [MrBearPresident/JBL_Soundbar](https://github.com/MrBearPresident/JBL_Soundbar) | 294 | `async_track_state_change` from `helpers.event`: [`number.py:7`](https://github.com/MrBearPresident/JBL_Soundbar/blob/9976c48755ad9d6725e281396c977a813cb9153b/custom_components/jbl_integration/number.py#L7) (+1 file) | affected entry fails setup |
| [soloam/ha-pid-controller](https://github.com/soloam/ha-pid-controller) | 102 | `async_track_state_change` from `helpers.event`: [`sensor.py:36`](https://github.com/soloam/ha-pid-controller/blob/60052392bdaa114dc9296fcf7d3b58db48129993/custom_components/pid_controller/sensor.py#L36) | that YAML platform fails |
| [starwarsfan/moving-colors](https://github.com/starwarsfan/moving-colors) | 16 | `async_track_state_change` from `helpers.event`: [`__init__.py:20`](https://github.com/starwarsfan/moving-colors/blob/18ed55e7a7cd44977408ba1e52b89ad7bf239c72/custom_components/moving_colors/__init__.py#L20) | affected entry fails setup |
| [MatthewOnTour/BUT_blinds_time_control](https://github.com/MatthewOnTour/BUT_blinds_time_control) | 14 | `async_track_state_change` from `helpers.event`: [`cover.py:24`](https://github.com/MatthewOnTour/BUT_blinds_time_control/blob/ca65c4e715eb81982b7d38aab146fbc0eda22c12/custom_components/blinds_controller/cover.py#L24) | that YAML platform fails |
| [Anonym-tsk/homeassistant-climate-xiaomi-remote](https://github.com/Anonym-tsk/homeassistant-climate-xiaomi-remote) | not reported | `async_track_state_change` from `helpers.event`: [`climate.py:20`](https://github.com/Anonym-tsk/homeassistant-climate-xiaomi-remote/blob/7b6fcbfc423804ee13c1b594db6e847551bb245b/custom_components/xiaomi_remote/climate.py#L20) | that YAML platform fails |
| [ChrisTracy/clickpi_garage_door](https://github.com/ChrisTracy/clickpi_garage_door) | not reported | `async_track_state_change` from `helpers.event`: [`cover.py:10`](https://github.com/ChrisTracy/clickpi_garage_door/blob/40beb88860ec7627386fc480b42e2f07593d8dc4/custom_components/clickpi_garage_door/cover.py#L10) | affected entry fails setup |
| [akasma74/Hass-Custom-Alarm](https://github.com/akasma74/Hass-Custom-Alarm) | not reported | `async_track_state_change` from `helpers.event`: [`alarm_control_panel.py:53`](https://github.com/akasma74/Hass-Custom-Alarm/blob/8c7b663783ceeb872bf2341296d0b39a2af87f68/custom_components/bwalarm/alarm_control_panel.py#L53) | that YAML platform fails |
| [elik745i/MQTT-Remote-Buttons-Remap](https://github.com/elik745i/MQTT-Remote-Buttons-Remap) | not reported | `async_track_state_change` from `helpers.event`: [`__init__.py:11`](https://github.com/elik745i/MQTT-Remote-Buttons-Remap/blob/9c4a2fc07a4e85ce860cbee1322a119062bd2d64/custom_components/mqtt_remote_buttons_remap/__init__.py#L11) | affected entry fails setup |

ev_smart_charging had an issue about the deprecation in 2024 (closed); ha-pid-controller has
an open issue and an unmerged pull request for it.

**Two smaller changes:**

| integration | opt-in installs | removed import (code at HEAD, October 18) | predicted effect on checked 2026.11 dev |
|---|---:|---|---|
| [dk-1983/Modbus_Devices](https://github.com/dk-1983/Modbus_Devices) | 3 | `async_get_unprefixed_name` from `helpers.entity_registry`: [`builder.py:114`](https://github.com/dk-1983/Modbus_Devices/blob/88460d5b9db9b7cb3abb0032de81a562522ec8b7/custom_components/modbus_devices/presentation/builder.py#L114) | fails when that code runs |
| [Anrolosia/ha-webauthn-mfa](https://github.com/Anrolosia/ha-webauthn-mfa) | not reported | `verify_client_id` from `components.auth.indieauth`: [`__init__.py:127`](https://github.com/Anrolosia/ha-webauthn-mfa/blob/b62b3d8aa854cb0976459fc60cb6a4f75cd1a2d3/custom_components/webauthn_mfa/__init__.py#L127) | fails when that code runs |

- `entity_registry.async_get_unprefixed_name` is removed. We did not check a replacement.
- `indieauth.verify_client_id` now requires the keyword arguments `request_scheme` and
  `request_netloc` ([#186543](https://github.com/home-assistant/core/pull/186543), merged
  October 17). ha-webauthn-mfa calls it with one argument while handling a login request,
  so that request raises `TypeError`. 2026.10 does not accept the new arguments.

## Check it yourself

[`check.py`](check.py) runs each removed import, then the replacement, on the installed Home
Assistant. It imports only Home Assistant and its own dependencies; it does not import or
run any integration.

```sh
python check.py
```

Output on `2026.11.0.dev0` (core `dev` at b19ddb39, Python 3.14.3). `raises` is what the
integrations do today; `fix` is the replacement. A `skip` line means a dependency of that
Home Assistant component is not installed, so the line could not be checked:

```text
Home Assistant 2026.11.0.dev0
raises  from homeassistant.components.script import ATTR_LAST_TRIGGERED: ImportError: cannot import name 'ATTR_LAST_TRIGGERED' from 'homeassistant.components.script'
   fix  ok      from homeassistant.components.script.const import ATTR_LAST_TRIGGERED
raises  from homeassistant.components.event import EventExtraStoredData: ImportError: cannot import name 'EventExtraStoredData' from 'homeassistant.components.event'
   fix  ok      from homeassistant.components.event.entity import EventExtraStoredData
raises  from homeassistant.components.text import RestoreEntity: ImportError: cannot import name 'RestoreEntity' from 'homeassistant.components.text'
   fix  ok      from homeassistant.helpers.restore_state import RestoreEntity
raises  from homeassistant.components.sensor import RestoreEntity: ImportError: cannot import name 'RestoreEntity' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.helpers.restore_state import RestoreEntity
raises  from homeassistant.components.input_boolean import RestoreEntity: ImportError: cannot import name 'RestoreEntity' from 'homeassistant.components.input_boolean'
   fix  ok      from homeassistant.helpers.restore_state import RestoreEntity
raises  from homeassistant.components.sensor import EntityCategory: ImportError: cannot import name 'EntityCategory' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.const import EntityCategory
raises  from homeassistant.components.sensor import UnitOfTemperature: ImportError: cannot import name 'UnitOfTemperature' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.const import UnitOfTemperature
raises  from homeassistant.components.climate import UnitOfTemperature: ImportError: cannot import name 'UnitOfTemperature' from 'homeassistant.components.climate'
   fix  ok      from homeassistant.const import UnitOfTemperature
raises  from homeassistant.components.sensor import CONF_UNIT_OF_MEASUREMENT: ImportError: cannot import name 'CONF_UNIT_OF_MEASUREMENT' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
raises  from homeassistant.components.sensor import StateType: ImportError: cannot import name 'StateType' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.helpers.typing import StateType
raises  from homeassistant.components.sensor import HomeAssistantError: ImportError: cannot import name 'HomeAssistantError' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.exceptions import HomeAssistantError
raises  from homeassistant.components.sensor import Entity: ImportError: cannot import name 'Entity' from 'homeassistant.components.sensor'
   fix  ok      from homeassistant.helpers.entity import Entity
raises  from homeassistant.components.persistent_notification import async_dispatcher_send: ImportError: cannot import name 'async_dispatcher_send' from 'homeassistant.components.persistent_notification'
   fix  ok      from homeassistant.helpers.dispatcher import async_dispatcher_send
raises  from homeassistant.components.time import time: ImportError: cannot import name 'time' from 'homeassistant.components.time'
   fix  ok      from datetime import time
raises  from homeassistant.components.sensor import datetime: ImportError: cannot import name 'datetime' from 'homeassistant.components.sensor'
   fix  ok      from datetime import datetime
raises  from homeassistant.components.sensor import dataclass: ImportError: cannot import name 'dataclass' from 'homeassistant.components.sensor'
   fix  ok      from dataclasses import dataclass
raises  from homeassistant.components.sensor import cached_property: ImportError: cannot import name 'cached_property' from 'homeassistant.components.sensor'
   fix  ok      from propcache.api import cached_property
raises  from homeassistant.components.camera import RTCIceCandidateInit: ImportError: cannot import name 'RTCIceCandidateInit' from 'homeassistant.components.camera'
   fix  ok      from webrtc_models import RTCIceCandidateInit
raises  from homeassistant.components.wake_on_lan import SERVICE_SEND_MAGIC_PACKET: ImportError: cannot import name 'SERVICE_SEND_MAGIC_PACKET' from 'homeassistant.components.wake_on_lan'
   fix  ok      from homeassistant.components.wake_on_lan.services import SERVICE_SEND_MAGIC_PACKET
raises  from homeassistant.components.zone import DATA_ZONE_STORAGE_COLLECTION: ImportError: cannot import name 'DATA_ZONE_STORAGE_COLLECTION' from 'homeassistant.components.zone'
raises  from homeassistant.helpers.entity_registry import async_get_unprefixed_name: ImportError: cannot import name 'async_get_unprefixed_name' from 'homeassistant.helpers.entity_registry'
raises  from homeassistant.helpers.event import async_track_state_change: ImportError: cannot import name 'async_track_state_change' from 'homeassistant.helpers.event'
   fix  ok      from homeassistant.helpers.event import async_track_state_change_event
raises  indieauth.verify_client_id(client_id): required keyword-only ['request_scheme', 'request_netloc']
```

On 2026.10.2, every removed import works and every replacement works except
`event.entity` and `wake_on_lan.services`; full output in
[`out-2026.10.2.txt`](out-2026.10.2.txt).

## Method and limits

- Frame: the HACS default `integration` list (3,241 repositories). 3,219 were cloned at
  HEAD on October 18; 22 failed to clone twice and were not read.
- We extracted every Home Assistant import and attribute use from the non-test Python files
  (440,046 uses, 6,111 distinct names) and resolved each name in 2026.10.2 and in `dev`.
  One file with a UTF-8 byte-order mark failed to parse; we read it by hand, and it imports
  none of the removed names.
  Every name that resolves in 2026.10.2 but not in `dev` was then imported on `dev` to
  confirm it fails. Names already missing in 2026.10.2 are not counted.
- Every repository with a hit was read by hand. A use counts only if it is not behind
  `TYPE_CHECKING`, a version check or a `try` that catches the error.
- The effect column comes from reading how each integration sets up its platforms, then
  applying the behaviour `entry_setup.py` shows. No integration was installed or run.
- Names reached dynamically (`importlib`, `getattr`) are missed, so this list is a floor.
- Core is the `dev` branch, not a release. The beta could still add a compatibility shim.
- Repositories outside the HACS default list are not covered.
- Installs are the `total` for each domain in Home Assistant's opt-in analytics
  (`analytics.home-assistant.io/custom_integrations.json`, October 18), across all versions.
- This is one run on our own machine, not an independent reproduction.

See also: [Home Assistant 2026.11: what still breaks after the maintainers'
outreach](../home-assistant-2026-11-breaks/), on the `DeviceInfo` and `last_states` changes.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
