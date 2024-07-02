# Readme

This is a custom component for the media_player platform of [Home Assistant][1].

It allows you to remotely control your AirMusic compatible internet radios. Should work with any radio using the AirMusic Android and iOS app for control.

# What is working:
  - Power status and power control: on, off, standby. 
  - Loads all sources from Internet Radio favorites. 
  - Information about current radio program.
  - Volume regulation (mute, set, step)
  - Change radio channel (Selecting from source list))
  - Current radio channel and current event
  - Supports authentication and multiple receivers

# What is not working right now:
  - No source selection, only Internet Radio is available
  - No icon of current station, for radios with authantication I can't get it to work, for the ones without the image does not update when changing station

# Minimum Requirements
  - Homeassistant core 2024.5.0

# Install:
To use the airmusic custom component, place the file `airmusic` directory from the root of
the repository in to the folder `~/.homeassistant/custom_components/` where
you have your home assistant installation

The custom components directory is inside your Home Assistant configuration directory.

This is how your custom_components directory should be:
```bash
custom_components
├── enigma
│   ├── __init__.py
│   ├── media_player.py
│   ├── manifest.json
│   └── airmusicapi.py
```
# Install with HACS:
It is possible to add it as a custom repository.

If you are using HACS, go to HACS -> Integrations and click on the 3 dots (top righ corner).
Then choose custom repositories, and add this repository url (https://github.com/DominikWrobel/airmusic/tree/main), choosing the Integration category.

That's it, and you will be notified by HACS on every release.
Just click on upgrade.

# Configuration Example:

```yaml 
airmusic:
  devices:
    - host: 192.168.0.142
      name: Radio kuchnia
    - host: 192.168.0.248
      name: Radio łazienka
```

The Internet radios need to have static IP set up.

# Known problems with installation

  - the device should be turned off when restarting Home Assistant
  - you may need to send init command before restarting HA, you can do this by typing in web browser: (http://192.168.0.248/init) or using curl: (curl -H 'Authorization: Basic c3UzZzRnbzZzazc6amkzOTQ1NHh1L14=' http://192.168.0.142/init)
  - after some time the radio may need to send init again
  - there is no real way to see if the radio is in stanby mode, so the integration usus the value SID=1 when in stanby, but this also says the playback is stopped.

![1](https://github.com/DominikWrobel/airmusic/assets/89667597/28fb6ac6-ef21-4552-a183-397a5ac08825)

![2](https://github.com/DominikWrobel/airmusic/assets/89667597/a22cdfd1-31da-4774-9fd4-916758d5e019)

# Special thanks to:

Cinzas and his Enigma2 custom_component on whitch this integration is based upon: (https://github.com/cinzas/homeassistant-enigma-player/tree/master)

edberoi for creating python airmusicapi: (https://github.com/edberoi/python-airmusicapi/tree/main)

tabacha for dabman-api: (https://github.com/tabacha/dabman-api) 

RobinMeis for more info on the radio api: (https://github.com/RobinMeis/AirMusic/blob/master/README.md)

and to msp1974 from Home Assistant forum for his help with Python!
