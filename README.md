[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# Home Assistant sensor for german AWB waste collection schedule

## Installation:
### Manual
Copy all files from custom_components/awb/ to custom_components/awb/ inside your config Home Assistant directory.
### Hacs
Add this repo in the settings as integration then install and restart home assistant

## Discussion
https://community.home-assistant.io/t/awb-waste-collection-schedule/140486

## Find street number and street code:
https://www.offenedaten-koeln.de/dataset/strassenverzeichnis  
Strassenverzeichnis Standard 2015 -> Vorschau  
  
Domkloster 4, 50667 Köln:
 ```
street_code: 745
street_number: 4
```

## sensor
```
- platform: awb
  name: awb
  scan_interval: 3600
  street_code: 745
  street_number: 4
```

## customize
```
sensor.awb:
  friendly_name: Heute Mülltonne rausstellen
  icon: mdi:delete
```

## automation
```
- alias: AWB Notification
  trigger:
    - platform: time
      at: "18:00:00"
    - entity_id: binary_sensor.someone_is_home
      from: 'off'
      platform: state
      to: 'on'
  condition:
    - condition: and
      conditions:
      - condition: time
        after: '09:00:00'
      - condition: time
        before: '23:00:00'
      - condition: template
        value_template: "{{ (states.sensor.awb.state != 'Keine') and (states.sensor.awb.state != 'unknown') }}"
  action:
    - service: notify.my_telegram
      data_template:
        message: "{{ states.sensor.awb.name }}: {{  states.sensor.awb.state }}"
```
