# TO-DO
- [ ] create how-to in this repo and generally useful README
- [ ] grab the last frame (maybe more? config file?) of each video and save them separately, making some sort of other timelapse over multiple days with those
- [ ] integrate into HA for easier access, gemini can theoretically help with that
- [ ] update index.html to be less brittle with logfile names and cam names
- [ ] add today's sunrise/sunset times to index.html
- [ ] add notes about example files into README

# NOTES
## how it works 
* `record.py` is a script with the camera access and saved video mods in it and is command-line-callable
* `scheduler_sun.py` gets the sunrise time, current time, then waits until configured time relative to sunrise, and calls record.py to record sunrise
* these both go into crontab to be run automatically
  * crontab can be accessed and edited directly with `sudo crontab -e` to see what the cript arguments and time settings are. 
  * occasional backups of crontab config are made and pushed here for saving. Backup made with `crontab -l > crontab.bak`

## Web server
current root: `<this_dir>/webroot`
config file: /etc/nginx/sites-available/default 
command to restart after changes: `sudo systemctl restart nginx`
`index.html` is copied into this repo in order to have it all saved along side code, but lives in current root
