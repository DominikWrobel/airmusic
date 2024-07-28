# Remote

Using shell_command.yaml which you add to your configuration.yaml and remote.yaml to copy to your dashboard you can have a sumple remote with button cards in vertical and horizontal stack. Make sure you change the IP adress and the media_player entity of the radio! This remote can be used with or without the airmusic integration!

![remote](https://github.com/DominikWrobel/airmusic/assets/89667597/0eed7dc5-3f92-4b3b-89c2-7309967f85a0)

# Available remote buttons

For self init button you can use this code:

kuchnia_init: "curl -H 'Authorization: Basic c3UzZzRnbzZzazc6amkzOTQ1NHh1L14=' http://192.168.0.142/init?language=pl" 

change the language= to your language.

Change the value at the end of Sendkey?key=

|ID |   Function    |
|---|---------------|
|1  | Home          |
|2  | Up            |
|3  | Down          |
|4  | Left          |
|5  | Right         |
|6  | Enter         |
|7  | On / Off      |
|8  | Mute / Unmute |
|9  | Volume Up     |
|10 | Volume Down   |
|11 | Alarm clock   |
|12 | Sleep Timer   |
|13 | Language      |
|14 | Screen dim    |
|15 | Favourites    |
|19 | EQ            |
|28 | Mode          |
|29 | Play / Pause  |
|30 | Stop          |
|31 | Next Track    |
|32 | Previous Track|
|36 | USB           |
|40 | IntenretRadio |
|105| PowerSaving   |
|106| EqualizerFlat |
|110| SystemMenu    |
|111| WPS           |
|112| NextFav       |
|113| DAB           |
|115| "1"           |
|116| "2"           |
|117| "3"           |
|118| "4"           |
|119| "5"           |
|120| "6"           |
|121| "7"           |
|122| "8"           |
|123| "9"           |
|124| "10"          |

# Add new favourite station:

With this script, helpers and shell_command you can add a new favourite station directly to your radio form Home Assistant!

First add three helpers:
 - input_select named Radio IP and add your radio IPs to select (you can skip this if you have only one Airmusic radio)
 - imput_text named Station Name
 - input_text named Station URL

Add a new shell_command to your configuration.yaml:

```
shell_command:
  add_radio_station: >
    curl -H 'Authorization: Basic c3UzZzRnbzZzazc6amkzOTQ1NHh1L14=' 
    'http://{{ states("input_select.radio_ip") }}/AddRadioStation?name={{ states("input_text.station_name") | urlencode }}&url={{ states("input_text.station_url") | urlencode }}'
```

If you have only one Airmusic radio change {{ states("input_select.radio_ip") }} to your radio IP.

Creat a new script and paste this:

```
alias: Add new station
sequence:
  - service: shell_command.add_radio_station
    data: {}
  - service: persistent_notification.create
    data:
      title: Radio Station Added
      message: >
        Added station "{{ states("input_text.station_name") }}"  with URL "{{
        states("input_text.station_url") }}"  to radio at {{
        states("input_select.radio_ip") }}
description: ""
icon: mdi:radio
```

Restart Home Assistant. Then add in any dashboard you want an entities card with this code, with one radio skip the input_select part:

```
type: entities
entities:
  - entity: input_select.radio_ip
  - entity: input_text.station_name
  - entity: input_text.station_url
  - entity: script.add_new_station
```

![nowa](https://github.com/user-attachments/assets/fd77fc73-7c77-4e99-ac02-31129cb4109c)

Fill out all the fields and hit run, you will get a notification that new station has been added. Remember to reload the Airmusic integration to see the new station in your media_player card!
