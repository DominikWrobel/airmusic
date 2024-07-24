# Readme

This is a custom component for the media_player platform of Home Assistant. 

It allows you to remotely control your AirMusic compatible internet radios. Should work with any radio using the AirMusic Control Android or iOS app (https://play.google.com/store/apps/details?id=air.net.mediayou.AirMusicControlApp).

This incloudes brands like Oakcastle, Majority, Ferguson, Blow, Blaupunkt, Dual, Camry, TechniSat, Kruger&matz, Audizio, Dabman, Imperial, Soundmaster, Oneconcept, Lenco, Xoro, Technaxx, Sharp, Conrad’s

![icon](https://github.com/user-attachments/assets/295d78bc-64c9-4260-8e27-1deb0477cf38)

# What is working:
  - Power status and power control: on, off, standby. 
  - Loads all sources from Internet Radio favorites. 
  - Information about current radio program.
  - Volume regulation (mute, set, step)
  - Change radio channel (Selecting from source list)
  - Current radio channel and current event
  - Supports authentication and multiple receivers
  - Self INIT upon setup
  - Station logos work
  - Unique ID is now working
  - Setup via GUI only, yaml now depricated
  - Next track button set to next track in browse media mode, in internet mode next favourite.
  - Previous track button set to previous track in browse media mode, in internet mode sleep time., one press sets sleep time to 15 min, another one adds 15 min up until 180 min then it resets
  - Timer implemented for sleep time, works only when setup from this integration
  - EXPERIMENTAL media browser was implemented, from v1.7 local media via DLNA server work, Radio Browser works.

# What is not working right now:
  - No source selection, only Internet Radio is available
  - This integration will work correctly only in Internet Redio mode and using media browser

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
├── airmusic
│   ├── __init__.py
│   ├── media_player.py
│   ├── manifest.json
│   ├── airmusicapi.py
│   ├── config_flow.py
│   ├── const.py
│   ├── strings.json
│   ├── translations
│   │   └── en.json
```
# Install with HACS recomended:
It is possible to add it as a custom repository.

If you are using HACS, go to HACS -> Integrations and click on the 3 dots (top righ corner).
Then choose custom repositories, and add this repository url (https://github.com/DominikWrobel/airmusic), choosing the Integration category.

That's it, and you will be notified by HACS on every release.
Just click on upgrade.

# Configuration Example:
Search for Airmusic in Settings -> devices and services:

![airmusicint](https://github.com/user-attachments/assets/1c270b1b-b57a-4862-8c7d-080da2c12de5)

Type in your radio IP and name

![Przechwytywanie](https://github.com/user-attachments/assets/4e74103b-2ca9-43b6-a67a-82074f343fc8)

The Internet radios need to have static IP set up.

# Known problems with installation

  - At first installation the radio will receive init command, it may not work at first, try to turn on or off the radio and restart Home Assistant.
  - Do not use at the same time this integration and the AirMusic app or any other form of connecting to the radio via internet, it may cause the radio to freeze.


![1](https://github.com/DominikWrobel/airmusic/assets/89667597/c4b380e1-ffc7-4af3-84a3-8b54ec463657)

![Przechwytywanie](https://github.com/user-attachments/assets/19bf7125-bd2b-4152-ba95-7a1f63d1c5a4)

![album](https://github.com/user-attachments/assets/d7ff1719-38a8-4b89-99a9-31c1b49ac656)

![2](https://github.com/DominikWrobel/airmusic/assets/89667597/a22cdfd1-31da-4774-9fd4-916758d5e019)

# Remote and adding a new favourite radio station

I've added a simple remote at (https://github.com/DominikWrobel/airmusic/tree/main/remote) using shell_command and button cards. Remote can be used with or without this integration.

I've added a script, shell_command and helpers to add new favourite radio station from Home Assistant dashboard!

![nowa](https://github.com/user-attachments/assets/a1ff185a-f5cc-4a8a-91ec-4ae01738187d)

# Support

If you like my work you can support me via:

<figure class="wp-block-image size-large"><a href="https://www.buymeacoffee.com/dominikjwrc"><img src="https://homeassistantwithoutaplan.files.wordpress.com/2023/07/coffe-3.png?w=182" alt="" class="wp-image-64"/></a></figure>

# Special thanks to:

Cinzas and his Enigma2 custom_component on whitch this integration is based upon: (https://github.com/cinzas/homeassistant-enigma-player/tree/master)

edberoi for creating python airmusicapi: (https://github.com/edberoi/python-airmusicapi/tree/main)

tabacha for dabman-api: (https://github.com/tabacha/dabman-api) 

RobinMeis for more info on the radio api: (https://github.com/RobinMeis/AirMusic/blob/master/README.md)

and to msp1974 from Home Assistant forum for his help with Python!
