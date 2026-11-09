# 🧾 Changelog

All notable changes to this project will be documented in this file, following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

---

## [0.2.1] - 2026-11-09

### Fixed
- Z2M: turning the light off at the switch could turn it straight back on. Hue can report a brightness change while the light is still on, so `light_settled` fired just before `light_off` and the switch turn-on added to it in 0.2.0 turned the switch, and then the light, back on. `light_settled` now only updates the LED.

---

## [0.2.0] - 2026-11-08

### Added
- Zigbee2MQTT version of the dimmer blueprint (`hue_dimmer_z2m.yaml`) and a Z2M dimming script, alongside the ZHA versions (2026-02-06).
- ZHA: double tap up/down sets brightness to 100% / 10% (2025-07-25).
- ZHA: switch LED color follows the light's color (2025-10-19).
- ZHA: switch and Hue light state stay in sync in both directions (2025-07-11).
- Updated flow diagram in `docs/` (2025-07-12).

### Changed
- ZHA dimming script renamed `dim_hue_room_lights.yaml` → `dim_hue_room_lights_zha.yaml` (2026-02-06/09).
- README corrections and fixed import links (2025-07-12/13); blueprint descriptions and YAML formatting tidied (2026-02-09).

### Fixed
- Z2M: switch no longer stayed on when the Hue light was turned off from the Hue app or elsewhere. Turning a Hue light off also changes its `brightness`/`color_temp_kelvin` attributes, so the `light_settled` trigger fired right after `light_off` and, under `mode: restart`, cancelled it before the switch was turned off. Triggers that would do nothing (`light_settled` while the light is off, `switch_on`/`switch_off` when the light already matches) are now dropped in the top-level `condition:` block, which runs before the restart.
- Z2M: `light_settled` now also turns the switch on if it is off, in case a restart cancelled the `light_on` handler during its 300 ms delay.
- Z2M: switch LED stays in sync with the light, and warm/cool color temperatures map to the right LED color (2026-04-25).
- Z2M: MQTT topic handling and other Z2M bugs (2026-02-07 to 2026-04-25).
- ZHA: LED intensity (2025-10-19).

---

## [0.1.1] - 2025-06-29

### Added
- Visual setup diagram illustrating integration between Hue, ZHA-based Inovelli Blue switches, and Home Assistant helpers.
- Added troubleshooting info to the README documenting debug log examples and helper usage.
- Scene cycling automation with dynamic scene discovery using `input_number.scene_index_<room>`.
- Paddle dimming functionality via `input_boolean.dimmer_<room>` and `dim_hue_room_lights.yaml` script.
- Support for directional hold (up/down) with brightness adjustment logic.
- YAML templates referencing `room_slug` to standardize helper and scene naming.

### Changed
- Updated debug logs to standardize format and include helper states, active scenes, and light modes (e.g. `xy_color`).
- README enhancements to clarify helper setup and event mapping.

### Fixed
- Color mismatch between identical Hue bulbs by preferring `xy_color` mode in automations.
- Scene restoration logic to better preserve original color temperature vs color mode.

### Deprecated
- Manual scene list definitions — replaced with dynamic discovery via templates.

---

## [0.1.0] - 2025-06-29

Initial release of:
- Dimmer automation blueprint
- Scene cycler blueprint
- Light level script

Includes basic README and prerequisites checklist.
