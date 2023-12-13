[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)


# Preamble
Please note that you'll need to be logged in as `root` (command `sudo su`)
or to prepend `sudo` to most commands bellow, in particular for installation,
running or service interaction.

# Installation
## Raspberry Pi Configuration
The Raspberry Pi configuration is not covered by this installer as it depends
on the operating system you have installed. Nevertheless here are some
recommendations for the configuration.

### Raspi-Config
The following settings should be manually set using `raspi-config`:

If you have a recent system, you must activate legacy-camera support via:  
`3 Interface Options` > `I1 Legacy Camera` > `Enable`
On older system the options are sightly different: 
`3 Interface Options` > `1 Camera` > `Yes`

### Config File
The following settings should be set in the config file `/boot/config.txt`:

 - `disable_oversan=1` (Optional)
 - `dtparam=i2c_arm=on` (Optional)
 -  `dtparam=audio=off` (**Required** for LED operations)
 - `[pi4]` :
    - `dtoverlay=vc4-fkms-v3d`
    - `max_framebuffers=2` 
- `[all]`
    - `start_x=1` (Required for camera)
    - `gpu_mem=128`

#### Allow software to run as normal user
While this is theoritically feasable, this procedure **has not been tested** and
is therefore not recommended.  
To allow the software to run as normal user the following change would be required:
- Connect LED to D10 instead of D18 GPIO PIN
- set `open_micro_view.mm_microscope_lighy.LED_PIN` to `board.D10` before start()
- Change following configuration in `/boot/config.txt`:
 - `dtparam=spi=on`
 - `enable_uart=1`

> **Note**  
> Running the process as a normal user may provoke permission errors while
> saving, reading or copying pictures. Temperature may also not be available.

## Installation of OpenMicroView
Installation script is located in `install/` directory but should be run from
the root directory of the project. 

### One-liner installation
You can execute this command, it will do the same as below steps 1, 2, 3 and 4 in a single line.
```
git clone https://github.com/Space-Biology-Group/OpenMicroView --depth 1 && cd OpenMicroView && sudo install/install.sh -A
```

If you prefer to play it safe and control every steps, you can do it step by step as shown below.

### 1. Download the project

```sh
cd ~/Downloads/
git clone https://github.com/Space-Biology-Group/OpenMicroView
```

### 2. Install Dependencies
To install dependencies, run the following command as root: 
```sh
install/install.sh -D
```

### 3. Installing as Service (optional)
To install OpenMicroView as a service, run the following command as root: 
```sh
install/install.sh -S
```
The software will be copied in `/opt/OpenMicroView/` and a service file
will be created in systemd directory.

### 4. Check your raspberry pi configuration
The install script allows you to check for classical configuration errors,
to do so you can just run the following command as root:
```sh
install/install.sh -C
```
### Note
You can see full usage of the installation tool using:
```sh
install/install.sh -h
```
or you can execute `-DSC` or `-A` to install dependencies and service, and also
check for configuration errors.

# Starting the interface
## Service
If you installed OpenMicroView as a Service, you can use the following commands
to start/stop/restart or view the status of OpenMicroView:
```sh
service OpenMicroView start
service OpenMicroView stop
service OpenMicroView restart
service OpenMicroView status
```
if you want to enable or disable the service to start at boot:
```sh
systemctl enable OpenMicroView.service
systemctl disable OpenMicroView.service
```
In order to view the logs from the service:
```sh
journalctl -u OpenMicroView
# add `-f` to follow logs in real time
```

## Standalone
To start the application as a standalone application, you can use the following 
command:
```sh
# Go inside project directory
cd OpenMicroView
# Start interface
sudo python3 ./start.py
```
> **NOTE**  
> If you want to connect via SSH, you'll need to locally start a terminal
> (`CTRL+T`) and open a screen session (`screen -q`). Then join this screen
> session from ssh using `screen -x`.


# Debugging
- `Authentication error`: prepend `sudo` (e.g. `sudo service OpenMicroView start`)
- The software doesn't start at all
    - Look at the logs with `journalctl -u OpenMicroView -f`
    - Verify 'camera' or 'Legacy Camera' is activated (`sudo raspi-config` 
      -> `3 Interface` > `1 (Legacy) Camera`)
    - If started using the service verify the following
        - open `/etc/systemd/system/OpenMicroView.service` 
        - Check `Environment="DISPLAY=<value>"`: `<value>` is equal to the
          output of `echo $DISPLAY` when executed directly on the targeted
          screen (`:0`, `:0.0`, ...).
        - Check `Environment="XAUTHORITY=/home/<user>/.Xauthority"`: `<user>`
          is you're normal user. You can execute `ls -1 /home/` to find the
          correct user. Choose default user if several exists.
        - if you make any changes, save, close and reload systemctl with
          `systemctl daemon-reload`
        - restart service with `service OpenMicroView stop`
- If the LED do not switch on correctly: 
    - Verify `/boot/config.txt` contains `dtparam=audio=off`
    - Verify LED is connected on `GPIO D18` connector
- If the Screen is not calibrated:
    - Most likely due to newer kernel reason. Investigation on going...

## Notes
This software has been tested and validated on the following system versions :
- `raspios_oldstable_armhf/2019-09-26` [Linux kernel 4.19.75]  [RPi firmware 01508e81ec1e918448227ca864616d56c430b46d]

The following system presented issues with the touchscreen:
- `raspios_oldstable_armhf/2023-05-03` [Linux kernel 5.10.103] [RPi firmware 638c7521ee0c431fafca1e2bd4fd25705b37ea5b]
