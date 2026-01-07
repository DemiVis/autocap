# Installation 
```
# 1. Download the latest release for ARM64 (Raspberry Pi 3/4/5)
wget https://github.com/bluenviron/mediamtx/releases/download/v1.6.0/mediamtx_v1.6.0_linux_arm64v8.tar.gz

# 2. Extract it
tar -xvzf mediamtx_v1.6.0_linux_arm64v8.tar.gz

# 3. Move it to a global bin location
sudo mv mediamtx /usr/local/bin/
```

# configuration
1. update with real streams and copy mediamtx.yml to `/usr/local/etc/mediamtx.yml`
2. setup as a service
  a. make the following file and save to `/etc/systemd/system/mediamtx.service`
    ```
    [Unit]
    Description=MediaMTX RTSP Server
    After=network.target

    [Service]
    ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
  b. enable and start the service
    ```
    sudo systemctl enable mediamtx
    sudo systemctl start mediamtx
    ```