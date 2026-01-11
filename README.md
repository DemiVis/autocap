# TO-DO
- [ ] create how-to in this repo and generally useful README
- [ ] grab the last frame (maybe more? config file?) of each video and save them separately, making some sort of other timelapse over multiple days with those
- [ ] integrate into HA for easier access, gemini can theoretically help with that
- [ ] add today's sunrise/sunset times to index.html
- [ ] fix eth0 mess, point internet at wlan only permanently, put details into README 
- [ ] make sure that fixes the time sync issue possiblity, put details into README
- [ ] fix permissions on the mounted drive so can make a "latest_sunrise" and "latest_sunset" symlink and make that symlink, then point HA to it
- [ ] add ability to capture single frames relative to sunrise/sunset time (to scheduler_sun.py)

# NOTES
## how it works 
A config file needs to be made and placed in this directory named `config.json` (see `example_config.json`). This specifies the webroot, logs dir, camera connection details and location/timezone details.

There is an nginx webserver running that serves index.html (needs to be copied to webroot directory). This file shows the single webpage for easy use. This webpage relies on a manifest of directories and log files (see indexer.py details below). 

There are a few scripts that are needed in order to do this:
* `record.py` is a script with the camera access and saved video mods in it and is command-line-callable. Uses `ffmpeg` through python submodule calls
* `scheduler_sun.py` gets the sunrise time, current time, then waits until configured time relative to sunrise, and calls record.py to record sunrise
* `indexer.py` gets all the cameras and logfiles and shoves their names into a json in the webroot so that index.html can show everything. all directories are treated as camera directories except if they're hidden (start with `.`), have `noshow` anywhere in the name, or are the logs directory.
* these all go into crontab to be run automatically
  * `indexer.py` should run regularly so that new files/folders/cameras can be seen quickly
  * crontab can be accessed and edited directly with `sudo crontab -e` to see what the cript arguments and time settings are. 
  * occasional backups of crontab config are made and pushed here for saving. Backup made with `crontab -l > crontab.bak`
  * an example crontab file is included with this repo (`crontab_example.bak`)but it needs to be installed to function (see above)

Obviously the local time must be setup correctly, so if you're having trouble getting network time (but have a 
network connection) you can run the following command to set the time based on the network once manually while
you wait for the background sync to work more accurately
`sudo date -s "$(wget -qSO- --max-redirect=0 google.com 2>&1 | grep Date: | cut -d' ' -f5-8)Z"` 

Sometimes the network breaks because the eth0 becomes the default route to the internet (even though it's on a VLAN with only the cameras). This can be temporarily repaird with
`sudo ip route del default via 192.168.1.1 dev eth0` 
should work to get the right routing tables setup for real (permanently) otherwise this command is needed frequently, but for now this works

## Web server Details
* running nginx with basic config to serve directories/files 
* current root: `<this_dir>/webroot`
* config file: /etc/nginx/sites-available/default 
* command to restart after changes: `sudo systemctl restart nginx`
* `index.html` is copied into this repo in order to have it all saved along side code, but lives in current webroot

## HA Connection
This is connected to HA in two ways.
1. Through the software at https://github.com/ironsheep/RPi-Reporter-MQTT2HA-Daemon in order to report on the system itself. This is installed and managed at `/opt/RPi-Reporter-MQTT2HA-Daemon` per repo recommendations
2. through things where more deatils will be added in forwarding camera streams and accessing the latest video from each cam
