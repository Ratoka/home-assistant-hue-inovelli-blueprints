[![Import Automation Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Finovelli%2Fhue_dimmer_zha.yaml) **ZHA Automation Blueprint**

[![Import Automation Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Finovelli%2Fhue_dimmer_z2m.yaml) **Z2M Automation Blueprint**

[![Import Script Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Finovelli%2Fdim_hue_room_lights_zha.yaml) **Script Blueprint**

[![Import Script Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FRatoka%2Fhome-assistant-hue-inovelli-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Finovelli%2Fdim_hue_room_lights_z2m.yaml) **Script Blueprint Z2M**


# 🏠 Home Assistant Inovelli Hue Blueprints

This repository contains **dynamic, reusable blueprints** for integrating Inovelli Blue Series dimmers with Philips Hue lights and scenes. These automations are designed for **state-aware, adaptive lighting control** that evolves with your Hue setup.

**Available for:**
- **ZHA Integration** (via `hue_dimmer_zha.yaml` and `dim_hue_room_lights_zha.yaml`)
- **Zigbee2MQTT Integration** (via `hue_dimmer_z2m.yaml` and `dim_hue_room_lights_z2m.yaml`) - Works with the default `zigbee2mqtt` MQTT topic

---

## ✨ Features

- **💡 Light On/Off Control**  
  - Single tap up: Turns Hue room **on**  
  - Single tap down: Turns Hue room **off**  
  - Double tap up: Turns light on to 100%  
  - Double tap down: Turns light on to 10%  
  - Works regardless of whether lights were last controlled by switch, app, or automation  
  - Optional: Automatically activates a default scene when turning on  

- **Unified Paddle Dimming**
  - Hold paddle: Smooth dim up/down
  - Release paddle: Stop dimming
  - Uses `input_boolean.dimmer_<room>` to control dimming loop

- **🎬 Scene Cycling (Button 3)**
  - Press: Cycle forward through Hue scenes
  - Hold: Cycle backward
  - Scenes are dynamically discovered per Hue room
  - Tracks state with `input_number.scene_index_<room>`

- **🧼 Clean Entity Naming Convention**
  - Relies on the Hue room name (no spaces)
  - Dynamically references needed helpers based on room name to ease deployment

---

## Overview
![Device Overview](/docs/assets/DeviceFlow.png)

---

## 🚀 Getting Started

1. **Create a Hue Room** in the Hue app (e.g. `MasterBedroom`).
2. **Create Helpers** in Home Assistant:
   - `input_boolean.dimmer_masterbedroom`
   - `input_boolean.sync_<room>`
   - `input_number.scene_index_masterbedroom`
3. **Add Hue Scenes to the room** in the Hue app (when you create the input number, the max number should be greater than the number of scenes you plan to have)
4. **Add Inovelli Blue Switch** in HomeAssistant ZHA
5. **Configure Switch in HomeAssistant**
   - Enable the Smart Bulb feature  
   - Enable Double tap up  
   - Enable Double tap down  
   - Set button delay to at least 1 (required for double tap)  
5. **Import Blueprints** from this repo:
   - `hue_dimmer_zha.yaml` (automation)
   - `dim_hue_room_lights.yaml` (script)
6. **Create the script from the blueprint** in HomeAssistant using the blueprint, create the script (reference your first 
light/swith, this will be dynamically updated by the each automation depending on what switch and button is pressed)
7. **Create the automation** in HomeAssistant using the blueprint.  Reference the switch, room/zone, script from step 6., 
and desired brightness step (faster/slower dimming)
8. **Enjoy**

---

## 🛠️ Requirements

For each room (e.g. `MasterBedroom`), create:

| Entity | Example | Purpose | Where to Configure
|--------|---------|---------|---------|
| Hue Light Group | MasterBedroom | Hue Room/Zone that allows for multiple lights to be controlled and have scenes assigned | Hue App |
| Input Boolean | `input_boolean.dimmer_masterbedroom` | Controls dimming loop | HomeAssistant |
| Input Boolean | `input_boolean.sync_masterbedroom` | Holds the desired state of the light. When the light is toggled from the switch or app, this holds the lights state to sync to the devices.  (EG. If the light is turned on from the app, this also turns on the switch) | HomeAssistant |
| Input Number | `input_number.scene_index_masterbedroom` | Tracks active scene index | HomeAssistant |
| Hue Scenes | Relax | Creates a room/zone scene that can be acctived by the switch or app | Hue App |

---

### 🛠️ Creating inputs

The inputs are used to allow a single automation to trigger on/off, dimming and scene rotations. 
A set of inputs are required per switch/automation.  Depending on your personal preference, 
these can be configured in the UI or via YAML.  Below provides steps for the HA UI. Examples of  
how to define the helps via YAML are listed under .examples/helpers.yaml.

### 🔘 input_boolean: Toggle Helper

This helper is used to enable or disable specific automations or modes.

**Steps to create:**
1. Go to **Settings > Devices & Services > Helpers**.
2. Click **+ Add Helper**, then select **Toggle**.
3. Set the name of the helper to match the requirements above
4. Optionally set the icon (e.g., `mdi:lightbulb-group`).
5. Click **Create**.

### 🎚️ input_number: Slider or Number Box

Use this helper to store values like the current scene index or delay intervals.

**Steps to create:**
1. Navigate to **Settings > Devices & Services > Helpers**.
2. Click **+ Add Helper**, then choose **Number**.
3. Configure the details:
   - **Name**: e.g., `current_scene_index`
   - **Minimum / Maximum**: Set appropriate range for the maximum number of scenes you plan to have (e.g., 0–10, and can be updated later)
   - **Step size**: Set increment (e.g., 1)
   - **Unit of measurement**: Optional (e.g., none or "index")
4. Click **Create**.

---

## 🔌 Z2M Setup: MQTT Sensors (Required for Zigbee2MQTT)

The Z2M automation requires an **MQTT sensor** per switch to listen to your switch's actions. This ensures only the relevant automation triggers, not all instances.

### 📝 Create MQTT Sensors

Add this to your `configuration.yaml` or in a separate YAML file (e.g., `mqtt.yaml` included by `!include`):

```yaml
mqtt:
  - sensor:
      # MQTT sensor for Kitchen Switch (adjust device name)
      - name: "kitchen_switch_action"
        state_topic: "zigbee2mqtt/kitchen_switch/action"
        expire_after: 1

      # MQTT sensor for Living Room Switch (adjust device name)
      - name: "living_room_switch_action"
        state_topic: "zigbee2mqtt/living_room_switch/action"
        expire_after: 1

      # MQTT sensor for Office Switch (adjust device name)
      - name: "office_switch_action"
        state_topic: "zigbee2mqtt/Office_Switch/action"
        expire_after: 1
```

### 🔑 Key Points:
- **Device name casing**: Match the exact Z2M device name casing (e.g., `Office_Switch_FanLight`)
- **MQTT topic pattern**: `zigbee2mqtt/<your_device_name>/action`
- **One sensor per switch**: Create an MQTT sensor for each Inovelli switch you want to control
- **Entity name format**: The sensor will be automatically named `sensor.<name>` (based on the name field)
- **Friendly name**: The `name:` field becomes the entity name. For example, `name: "kitchen_switch_action"` creates `sensor.kitchen_switch_action`

### ✅ Verify MQTT Sensors Work

1. Open **Developer Tools > States** in Home Assistant
2. Search for your sensor (e.g., `sensor.kitchen_switch_action`)
3. Press a button on your Inovelli switch
4. The sensor state should update with the action (e.g., `up_held`, `down_double`, `config_single`)

If it doesn't update, check:
- Z2M device name matches your MQTT topic exactly (including capitalization)
- MQTT integration is working and enabled
- Z2M is publishing to the correct topic (check with MQTT Explorer)

## 📁 Included Blueprints

### 🔧 Hue Paddle Dimming + Scene Cycling (ZHA)
- **Path**: `blueprints/automation/inovelli/hue_dimmer_zha.yaml`
- **Integration**: ZHA
- **Handles**:
  - Paddle dimming (start/stop)
  - Scene cycling (forward/back)
  - Light on/off control
  - Default scene activation
  - Detailed logging

### 🔧 Hue Paddle Dimming + Scene Cycling (Zigbee2MQTT)
- **Path**: `blueprints/automation/inovelli/hue_dimmer_z2m.yaml`
- **Integration**: Zigbee2MQTT (MQTT)
- **Requirements**: Template sensor (see Z2M Setup section below)
- **Functionality**: Same as ZHA version - all features identical

### 🎚️ Hue Room Dimmer - Dynamic Up/Down
- **Path**: `blueprints/script/inovelli/dim_hue_room_lights.yaml` (or `dim_hue_room_lights_z2m.yaml`)
- **Handles**:
  - Smooth dimming loop
  - Customizable brightness step
  - Parameterized by room, direction, and step
- **Note**: Script blueprint works with both ZHA and Z2M automations

---

## 🧪 Example Setup: Room = `MasterBedroom`

1. In the Hue app, create a room named `MasterBedroom`
   - Add lights to the room
   - Add scenes to the room
2. In Home Assistant, create the following helpers:
   - `input_boolean.dimmer_masterbedroom`
   - `input_boolean.sync_masterbedroom`
   - `input_number.scene_index_masterbedroom`
3. Create a script from the **Hue Room Dimmer** blueprint (only required for the first room):
   - Set `Room Name` to `masterbedroom`
   - Set `Direction` to `up` or `down`
   - Set `Brightness Step (%)` to your preferred brightness increment
5. Create an automation from the **Hue Paddle Dimming + Scene Cycling** blueprint:
   - Set `Inovelli Switch (ZHA)` to the Inovelli switch device, like `MasterBedroom_Switch`
   - Set `Inovelli Switch Entity` to the light entity of the switch, like `MasterBedroom_Switch` and will have a lightbulb icon
   - Set `Light Group (Hue Room or Zone)` to the Hue room/zones light entity, like `light.Masterbedroom`
   - Set `Dimming Script` to the script created in step 3, this script is reusable and should be used for all instances of this automation
   - Set `Brightness Step (%)` to the desired percentage - lower to slow and raise to speed dimming
   - If you prefer a specific scene when turning on your light, enable `Enable Default Scene` - this does slow the light turning on, the light will turn on with 
     the previously used scene, then will switch to your default.
   - If enabling a default scene, enter the scene name for the room, like `scene.materbedroom_read`

Now your Inovelli switch will:
- Tap up: Turn on `light.masterbedroom` (and optionally activate a default scene)
- Tap down: Turn off `light.masterbedroom`
- Hold: Dim up/down  
- Release: Stop dimming
- Button 3 press/hold: Cycle through Hue scenes press for forward, hold for backward
- Your Inovelli switch will turn on/off when the light is turned on/off from the app or other integration

---

## ⚠️ Common Pitfalls

| Issue | Fix |
|-------|-----|
| Scenes not cycling | Scenes are named by the room when created.  If you changed the name of the room, scenes do not automatically recreate.  Open the room and click the (...), then select recreate entity IDs to rename the scenes in the room.  Also check the naming of the input number variable |
| Dimming not working | Confirm `input_boolean.dimmer_<room>` exists and matches the room name |
| Lights not turning on/off | Verify the room name has no spaces<br>If you renamed the room, recreate the entity IDs by navigating to the room, the click the (...), then select recreate entity IDs |
| ZHA events not triggering | Verify correct event IDs in automation trigger |

---

## 🛠️ Troubleshooting: Debug Logging for Inovelli Hue Blueprints

These blueprints include detailed logging to help diagnose issues with dimming, scene cycling, and helper state tracking. Here's how to interpret and leverage the logs effectively.

---

## 🔍 What the Logs Show (Example: Office Room)

The blueprints output clear debug messages for key actions and decisions. Below are examples you'll see in the logs when using the `"Office"` room:

- **Scene Cycling Events**  

Cycling to scene.office_relax (index 1 of 4)

- **Helper Validation**  

input_boolean.dimmer_office is off — skipping dimming loop

- **Scene Restoration Attempts**  

Restoring previous scene: scene.office_reading

- **Error Handling**  

Scene scene.office_party not found — skipping

These logs are designed to provide context-aware feedback, especially when testing dynamic behavior like long-press dimming, scene cycling, or light mode fallbacks.

### 📋 Where to Find Logs

- Logs are output to **Home Assistant’s system log** (`Configuration > Settings > System > Logs`)
- Enable debug logging for automations by adding this to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    homeassistant.components.automation: debug
    homeassistant.components.script: debug

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