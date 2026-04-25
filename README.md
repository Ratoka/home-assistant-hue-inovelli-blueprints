[![Import Automation Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Finovelli%2Fhue_dimmer_zha.yaml) **ZHA Automation Blueprint**

[![Import Script Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Finovelli%2Fdim_hue_room_lights_zha.yaml) **ZHA Dimming Script Blueprint** *(required for ZHA)*

[![Import Automation Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Finovelli%2Fhue_dimmer_z2m.yaml) **Z2M Automation Blueprint**

> **Helper entity examples:** See [`examples/helpers_z2m.yaml`](examples/helpers_z2m.yaml) (Z2M) and [`examples/helpers_zha.yaml`](examples/helpers_zha.yaml) (ZHA) for ready-to-paste helper configurations.


# 🏠 Home Assistant Inovelli Hue Blueprints

This repository contains **dynamic, reusable blueprints** for integrating Inovelli Blue Series dimmers with Philips Hue lights and scenes. These automations are designed for **state-aware, adaptive lighting control** that evolves with your Hue setup.

**Available for:**
- **ZHA Integration** (via `hue_dimmer_zha.yaml`)
- **Zigbee2MQTT Integration** (via `hue_dimmer_z2m.yaml`)

---

## ✨ Features

- **💡 Light On/Off Control**
  - Single tap up: Turns Hue room **on**
  - Single tap down: Turns Hue room **off**
  - Double tap up: Turns light on to 100%
  - Double tap down: Turns light on to 10%
  - Optional: Automatically activates a default scene when turning on

- **🎚️ Unified Paddle Dimming**
  - Hold paddle: Smooth dim up/down (inline — no separate script needed for Z2M)
  - Release paddle: Stop dimming

- **🎬 Scene Cycling (Config Button)**
  - Press: Cycle forward through Hue scenes
  - Hold: Cycle backward
  - Scenes are dynamically discovered per Hue room
  - LED color/intensity updates to match the activated scene
  - Requires one `input_number` helper (optional — scene cycling disabled if not configured)

- **💡 LED Sync**
  - LED color mirrors the Hue room's light color
  - LED intensity mirrors the Hue room's brightness
  - LED switches to a configurable "off" color when the light is off

- **🔄 Bidirectional Sync**
  - Switch and Hue room always stay in sync
  - Works whether the light is changed from the switch, the Hue app, or Home Assistant

---

## Overview
![Device Overview](/docs/assets/DeviceFlow.png)

---

## 🚀 Getting Started (ZHA)

1. **Create a Hue Room** in the Hue app (e.g. `Bedroom`). Room name must have no spaces.
2. **Add Hue Scenes** to the room in the Hue app.
3. **Add your Inovelli Blue switch** to Home Assistant via ZHA.
4. **Configure the switch** in Home Assistant:
   - Enable Smart Bulb mode
   - Enable Double Tap Up / Double Tap Down
   - Set button delay to at least 1 (required for double tap)
5. **Create the required helper entities** for each room (see [ZHA — Requirements](#zha--minimum-onoff-dimming-led-sync) below).
6. **Import both ZHA blueprints** using the buttons at the top of this page — the automation **and** the dimming script.
7. **Create a script** from the dimming script blueprint. No inputs need to be filled in; the automation passes them at runtime.
8. **Create an automation** from the ZHA automation blueprint and fill in:
   - **Inovelli Switch (ZHA)** — the ZHA device
   - **Inovelli Switch Entity** — the light entity of the switch (controls LED bar)
   - **Light Group (Hue Room or Zone)** — the Hue room entity (e.g., `light.bedroom`)
   - **Dimming Script** — the script entity you created in step 7
   - **Dimming Speed** — brightness change per step (lower = slower)
   - **LED Color When Off** — Inovelli LED color when light is off (0–255, 24 = warm white)
   - *(Optional)* **Enable Default Scene / Default Scene** — scene to activate on every turn-on
9. **Enjoy.**

> The room name is derived automatically from the Hue light group entity (e.g. `light.bedroom` → room = `bedroom`). All helper entity IDs must match this derived name exactly.

---

## 🛠️ Requirements (ZHA)

### ZHA — Minimum (on/off, dimming, LED sync)

| Entity | Example | Purpose | Where to Create |
|--------|---------|---------|-----------------|
| Input Boolean (dimmer) | `input_boolean.dimmer_bedroom` | Controls the dimming loop | Settings → Helpers → Add → Toggle |
| Input Boolean (sync) | `input_boolean.sync_bedroom` | Prevents sync trigger loops | Settings → Helpers → Add → Toggle |

### ZHA — With Scene Cycling

In addition to the two booleans above:

| Entity | Example | Purpose | Where to Create |
|--------|---------|---------|-----------------|
| Input Number | `input_number.scene_index_bedroom` | Tracks active scene index | Settings → Helpers → Add → Number |

Configure the input_number with min: `0`, max: `99`, step: `1`.

> A ready-to-paste example for bedroom and office rooms is in [`examples/helpers_zha.yaml`](examples/helpers_zha.yaml).

> **Scene naming:** Scenes must follow the `scene.<room>_<name>` pattern to be auto-discovered. In the Hue app, scenes are named this way automatically when created inside a room. If you renamed a room, open the room → `(...)` → **Recreate entity IDs**.

---

## 🧪 Example Setup (ZHA): Room = `Bedroom`

1. In the Hue app, create a room named `Bedroom` (no spaces)
   - Add lights to the room
   - Add scenes (e.g., `Relax`, `Energize`, `Read`)
2. In Home Assistant, create the required helpers:
   - **Settings → Helpers → Add → Toggle** → Name: `Dimmer - Bedroom` → entity: `input_boolean.dimmer_bedroom`
   - **Settings → Helpers → Add → Toggle** → Name: `Sync - Bedroom` → entity: `input_boolean.sync_bedroom`
   - *(Optional)* **Settings → Helpers → Add → Number** → Name: `Scene Index - Bedroom` → entity: `input_number.scene_index_bedroom` → Min: `0`, Max: `99`, Step: `1`
3. Import the ZHA dimming script blueprint and create a script from it (no configuration needed).
4. Import the ZHA automation blueprint and create an automation:
   - **Inovelli Switch (ZHA)**: your ZHA device
   - **Inovelli Switch Entity**: `light.bedroom_switch` (your switch's light entity)
   - **Light Group**: `light.bedroom`
   - **Dimming Script**: the script you created in step 3
   - **Brightness Step**: `10` (adjust to taste)

Your Inovelli switch will now:
- **Tap up**: Turn on `light.bedroom`
- **Tap down**: Turn off `light.bedroom`
- **Double tap up**: Set `light.bedroom` to 100%
- **Double tap down**: Set `light.bedroom` to 10%
- **Hold up/down**: Dim smoothly; release to stop
- **Config press/hold**: Cycle through Hue scenes (if scene helper is configured)
- **LED**: Reflects room color and brightness; off-state color when light is off
- **Hue app / HA changes**: Switch and light stay in sync automatically

---

## 🚀 Getting Started (Z2M)

1. **Create a Hue Room** in the Hue app (e.g. `Bedroom`). Room name must have no spaces.
2. **Add Hue Scenes** to the room in the Hue app.
3. **Add your Inovelli Blue switch** to Home Assistant via Zigbee2MQTT.
4. **Configure the switch** in Home Assistant:
   - Enable Smart Bulb mode
   - Enable Double Tap Up / Double Tap Down
   - Set button delay to at least 1 (required for double tap)
5. **Import the Z2M blueprint** using the button at the top of this page.
6. **Create an automation** from the blueprint and fill in:
   - **Z2M Action Sensor** — the custom MQTT sensor you created (e.g., `sensor.bedroom_switch_action`). See the [Z2M Action Sensor](#-z2m-action-sensor) section below.
   - **Inovelli Switch Light Entity** — the light entity of the switch (controls LED bar)
   - **Hue Light Group** — the Hue room or zone entity (e.g., `light.bedroom`)
   - **Z2M Device Name** — the friendly name in Zigbee2MQTT (e.g., `bedroom_switch`)
   - **Dimming Speed** — brightness change per step (lower = slower)
   - **LED Color When Off** — Inovelli LED color when light is off (0–255, 24 = warm white)
   - *(Optional)* **Scene Index Helper** — entity ID of an `input_number` helper for scene cycling
   - *(Optional)* **Default Scene** — scene to activate on every turn-on
7. **Enjoy.**

> No script blueprint or manual MQTT sensor configuration is required.

---

## 🛠️ Requirements (Z2M)

### Z2M — Minimum (on/off, dimming, LED sync)

No helper entities required. Only the automation blueprint is needed.

### Z2M — With Scene Cycling

| Entity | Example | Purpose | Where to Create |
|--------|---------|---------|-----------------|
| Input Number | `input_number.bedroom_scene_index` | Tracks active scene index | Settings → Helpers → Add → Number |

Configure the input_number with min: `0`, max: `99`, step: `1`.

> A ready-to-paste example for bedroom and office rooms is in [`examples/helpers_z2m.yaml`](examples/helpers_z2m.yaml).

> **Scene naming:** Scenes must follow the `scene.<room>_<name>` pattern to be auto-discovered. In the Hue app, scenes are named this way automatically when created inside a room. If you renamed a room, open the room → `(...)` → **Recreate entity IDs**.

---

## 🔌 Z2M Action Sensor

The blueprint needs an MQTT sensor that reports button presses from your switch.

> **Note:** Newer versions of Zigbee2MQTT do not expose an action sensor in Home Assistant by default. You must create the sensor manually as described below.

### Required: Custom MQTT Sensor (with `expire_after`)

Add this to your `configuration.yaml` (or a file included by it):

```yaml
mqtt:
  sensor:
    - name: "bedroom_switch_action"
      state_topic: "zigbee2mqtt/bedroom_switch/action"
      icon: mdi:access-point
      expire_after: 1
```

- **`name`**: Creates `sensor.bedroom_switch_action` in HA
- **`state_topic`**: Must match your Z2M device's MQTT topic exactly (case-sensitive). The device name is the friendly name shown in the Zigbee2MQTT dashboard.
- **`expire_after: 1`**: Resets the sensor to `unavailable` after 1 second. This is required so that repeated presses of the same button action (e.g., cycling scenes twice with `config_single`) each trigger the automation.

Restart Home Assistant after adding the sensor.

> A ready-to-paste example for bedroom and office switches is in [`examples/helpers_z2m.yaml`](examples/helpers_z2m.yaml).

### Alternative: Auto-Created Z2M Sensor

Older versions of the Z2M HA integration may create an action sensor automatically. You can use it without any `configuration.yaml` changes, but **repeated presses of the same button action will not re-trigger the automation** (the state doesn't change if the same action fires twice). This means cycling scenes multiple times with a single `config_single` press will only work every other press.

**To find your auto-created action sensor:**
1. Press any button on your Inovelli switch
2. Go to **Developer Tools → States**
3. Search for `sensor.<device_name>_action` (e.g., `sensor.bedroom_switch_action`)

**Verify the sensor works:**
- The state should change each time you press a button (e.g., `up_single`, `down_held`, `config_single`)
- If it doesn't update, confirm Z2M is running and the device is paired

---

## 🧪 Example Setup (Z2M): Room = `Bedroom`

1. In the Hue app, create a room named `Bedroom` (no spaces)
   - Add lights to the room
   - Add scenes (e.g., `Relax`, `Energize`, `Read`)
2. *(Optional)* In Home Assistant, create one helper for scene cycling:
   - **Settings → Helpers → Add → Number**
   - Name: `Bedroom Scene Index` → entity: `input_number.bedroom_scene_index`
   - Min: `0`, Max: `99`, Step: `1`
3. Import the Z2M blueprint and create an automation:
   - **Z2M Action Sensor**: `sensor.bedroom_switch_action`
   - **Inovelli Switch Light Entity**: `light.bedroom_switch` (your switch's light entity)
   - **Hue Light Group**: `light.bedroom`
   - **Z2M Device Name**: `bedroom_switch`
   - **Dimming Speed**: `10` (adjust to taste)
   - **Scene Index Helper**: `input_number.bedroom_scene_index` *(optional)*

Your Inovelli switch will now:
- **Tap up**: Turn on `light.bedroom`
- **Tap down**: Turn off `light.bedroom`
- **Double tap up**: Set `light.bedroom` to 100%
- **Double tap down**: Set `light.bedroom` to 10%
- **Hold up/down**: Dim smoothly; release to stop
- **Config press/hold**: Cycle through Hue scenes (if scene helper is configured)
- **LED**: Reflects room color and brightness; off-state color when light is off
- **Hue app / HA changes**: Switch and light stay in sync automatically

---

## ⚠️ Common Pitfalls

| Issue | Fix |
|-------|-----|
| Scenes not cycling | Scenes must follow `scene.<room>_*` naming. In the Hue app, open the room → `(...)` → **Recreate entity IDs** to fix renamed rooms. Also verify the Scene Index Helper entity ID is entered correctly. |
| Action sensor not found | Press a button on the switch, then search Developer Tools → States for `_action`. Confirm Z2M is running and the device is paired. |
| Wrong Z2M device name | The Z2M Device Name must exactly match the friendly name in the Z2M dashboard (case-sensitive). |
| Lights not turning on/off | Verify the Hue room entity name has no spaces. If you renamed the room, recreate entity IDs in the Hue app. |
| LED color not updating | Confirm the Z2M Device Name matches your Z2M config exactly. |

---

## 🔍 Resources

- [Blueprint Exchange Thread](https://community.home-assistant.io/t/inovelli-blue-zha-hue-lights/910208)
- [Inovelli Blue Devices](https://inovelli.com/collections/inovelli-blue-series)
- [Inovelli Blue Devices ZHA Documentation](https://help.inovelli.com/en/articles/8452425-blue-series-dimmer-switch-setup-instructions-home-assistant-zha)
- [Philips Hue Integration](https://www.home-assistant.io/integrations/hue/)
- [Philips Hue App Documentation](https://www.philips-hue.com/en-us/explore-hue/apps/bridge)
- Created by [@Ratoka](https://github.com/Ratoka)

---

## 📜 License

See the LICENSE file
