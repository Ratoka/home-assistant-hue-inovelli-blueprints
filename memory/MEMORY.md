# Project: Home Assistant Hue + Inovelli Blueprints

## Key Architecture Decisions

### Z2M Blueprint (hue_dimmer_z2m.yaml)
- **mode: restart** is intentional — it terminates the inline dimming loop when release fires
- Dimming is inlined using `repeat...until: false` (infinite loop killed by restart)
- Sync is trigger-based (specific `from/to` state transitions) — no `input_boolean.sync_<room>` needed
- LED update and default scene run **before** switch turn-on in `light_on` handler to avoid being killed by the subsequent `switch_on` restart
- `switch_on` and `switch_off` handlers have state checks (`states(light_entity) != 'on'`) to prevent loops
- Z2M action freshness condition (`< 30s`) prevents spurious triggers after HA restart
- MQTT payload for LED uses Z2M property names: `ledColorWhenOn`, `ledIntensityWhenOn`, `ledColorWhenOff`, `ledIntensityWhenOff`

### ZHA Blueprint (hue_dimmer_zha.yaml)
- Not modified (no test hardware available for ZHA)

## Helper Requirements
- Z2M: Zero required helpers for on/off/dimming/sync
- Z2M: One optional `input_number` helper for scene cycling (any entity name)
- ZHA: Still requires `input_boolean.dimmer_<room>`, `input_boolean.sync_<room>`, `input_number.scene_index_<room>`, and separate script blueprint

## Scene Discovery
- Scenes matched via prefix: `scene.<room_lower>_*`
- Room is derived from the Hue light entity: `light_entity.split('.')[1] | lower`
- Scenes must be created in the Hue app inside the room to get the correct prefix

## Z2M LED Control
- LED colors set via MQTT publish to `zigbee2mqtt/<z2m_device_name>/set`
- User provides `z2m_device_name` as a text input (friendly name in Z2M dashboard)
- Action sensor is auto-created by the Z2M HA integration — no manual MQTT sensor config needed
