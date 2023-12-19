[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)


# Preamble
Please note that you'll need to be logged in as `root` (command `sudo su`)
or to prepend `sudo` to most commands bellow, in particular for installation,
running or service interaction.

# Installation
## Raspberry Pi Configuration
Part of the Raspberry Pi configuration is covered by this installer when using
the `-E` or `-A` options:

### Raspi-Config
The following Camera can be manually activated using `raspi-config`:

If you have a recent system, you must activate legacy-camera support via:  
`3 Interface Options` > `I1 Legacy Camera` > `Enable`
On older system the options are sightly different: 
`3 Interface Options` > `1 Camera` > `Yes`

That will automatically add the following lines at the end of `/boot/config.txt`
```toml
[all]
start_x=1
gpu_mem=128
```
### Config File
In order for the LEDs to work correctly, the following setting should be set in
the config file `/boot/config.txt`:
```toml
dtparam=audio=off
```

### Not covered
Network or user configuration is not covered by the installer as it depends on
your setup. During our tests the default user was used, and the connection to
the network was established via cable.

#### Allow software to run as normal user
While this is theoritically feasable, this procedure **has not been tested** and
is therefore not recommended.  
To allow the software to run as normal user the following change would be required:
- Connect LED to D10 instead of D18 GPIO PIN
- In file `src/open_micro_view/microscope_light.py`, change constant `LED_PIN` 
  to `board.D10`
- In `/boot/config.txt` verify/change or add the config:
  ```toml
  dtparam=spi=on
  enable_uart=1
  ```


> **Note**  
> Running the process as a normal user may provoke permission errors while
> saving, reading or copying pictures. The setup of directory permissions are
> not detailled here.

## Installation of OpenMicroView
Installation script is located in the `install/` directory.

### One-liner installation
You can execute this command, it will do the same as below steps 1, 2, 3, 4 and
5 in a single line.
```sh
git clone ssh://git@github.com/SpaceBiologyGroup/OpenMicroView --depth 1 && sudo OpenMicroView/install/install.sh -A
```
Once done, if no error happened you can reboot the Raspberry Pi with
`sudo reboot`.

If you prefer to control every steps, you can do it step by step as shown below.

### 1. Download the project

```sh
git clone ssh://git@github.com/SpaceBiologyGroup/OpenMicroView --depth 1
```

### 2. Install Dependencies
To install dependencies, run the following command as root: 
```sh
OpenMicroView/install/install.sh -D
```

### 3. Installing as Service (optional)
To install OpenMicroView as a service, run the following command as root: 
```sh
OpenMicroView/install/install.sh -S
```
The software will be copied in `/opt/OpenMicroView/` and a service file
will be created in the systemd directory.

### 4. Check your raspberry pi configuration
The install script allows you to check for classical configuration errors,
To do so you can just run the following command as root:
```sh
OpenMicroView/install/install.sh -C
```

If every check succeed, the output should look like that:
```
 [ OK ] OS Version XXXX-XX-XX has been tested and validated
 [INFO] Checking '/boot/config.txt'...
 [ OK ] /boot/config.txt: 'dtparam=audio=off' is set
 [ OK ] /boot/config.txt: 'start_x=1' is set
 [ OK ] /boot/config.txt: 'gpu_mem=128' is set
 [INFO] Checking Service configuration...
 [ OK ] OpenMicroView Service is installed.
 [ OK ] /etc/systemd/system/OpenMicroView.service: 'DISPLAY="' error absent
 [ OK ] /etc/systemd/system/OpenMicroView.service: XAUTHORITY path seems correct
 [INFO] Reboot may be required if you edited the configuration.
```
### 5. Automatically Fix
If required you can try to automatically fix the `/boot/config.txt` file with:
```sh
OpenMicroView/install/install.sh -E
```
then, run step `4.` Once again to check the final config.

### 6. Reboot
Reboot the system (`sudo reboot`). Then, OpenMicroView UI should show up at start.

### Note
You can see full usage of the installation tool using:
```sh
install/install.sh -h
```
or you can execute `-DSEC` or `-A` to install dependencies, service, and 
to check for configuration errors.

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
> **Note**  
> If you want to connect via SSH, you'll need to locally start a terminal
> (`CTRL+T`) and open a screen session (`screen -q`). Then join this screen
> session from ssh using `screen -x`.


# Debugging
- `Authentication error`:
  - Make sure you are login as root or you prepended `sudo` (e.g. `sudo service OpenMicroView start`)
- The software doesn't start at all
  - Look at the logs with `journalctl -u OpenMicroView -f`
  - Verify 'camera' or 'Legacy Camera' is activated (`sudo raspi-config` 
    -> `3 Interface` > `1 (Legacy) Camera`)
  - If started using the service verify the following
    - open `/etc/systemd/system/OpenMicroView.service` 
    - Check `Environment="DISPLAY=<value>"`: `<value>` is equal to the
      output of `echo $DISPLAY` when executed directly on the targeted
      screen, not from SSH session (`:0`, `:0.0`, ...).
    - Check `Environment="XAUTHORITY=/home/<user>/.Xauthority"`: `<user>`
      is you're normal user. You can execute `ls -1 /home/` to find the
      correct user. Choose default user if several exists.
    - if you make any changes, save, close and reload systemctl with
      `systemctl daemon-reload`
    - restart service with `service OpenMicroView stop`
- Run `OpenMicroView/install/install.sh -C` to check the configuration
  - If error are found, run `OpenMicroView/install/install.sh -E` to fix them.
- If the LED do not switch on correctly: 
  - Verify `/boot/config.txt` contains `dtparam=audio=off`
  - Verify LED is connected on `GPIO D18` connector
- If the Screen is not calibrated:
  - This is likely due to kernel compatibility issue
  - Use one of the Compatible OS [listed below](#operating-system)
- If the screen stays OFF:
  - Verify connection of the screen to the raspberry
  - Make sure you are using one  of the [compatible versions](#operating-system)
  - Connect via SSH for debugging
- If the camera is not detected:
  - Verify it is activated using `raspi-config`  
  - Reboot the system
  - Make sure you are using one  of the [compatible versions](#operating-system)
- Verify current system version with `cat /boot/issue.txt`


# Versions
## Hardware
The software has been developped, tested and validated to run on a **RaspberryPi 3B**.  
Using Raspberry Pi 4 would result in hardware compatibility issues with the case of the OpenMicroView
microscope. Nevertheless, although it was not yet tested and it is therefore not recommended,
RaspberryPi 5 could be compatible (TBC) as the USB/Network port have the same location as the
RaspberryPi 3B.

## Operating System
[See on RaspberryPi Website](https://downloads.raspberrypi.com/raspios_oldstable_armhf/images/)

OpenMicroView has been tested and validated on the following system versions:

| RPi |      Image              |  Release   | Kernel  |    RPi Firmware Hash     | 
|-----|-------------------------|------------|---------|--------------------------|
| 3B  | raspios_oldstable_armhf | 2019-07-10 | 4.19.75 | `175dfb027ffabd4b8d5080097af0e51ed9a4a56c` |
| 3B  | raspios_oldstable_armhf | 2021-12-02 | 5.10.63 | `fa45ccf5a4b183ee566b36d74fb4b65bf9358bed` |
| 3B  | raspios_oldstable_armhf | 2022-01-28 | 5.10.63 | `60f6a26ed5701eec6be5c864dd0db48fe6244fad` |
| 3B  | raspios_oldstable_armhf | 2022-04-04 | 5.10.103| `910e079df1266036159ce4ea2aaa2ba9976ea3f1` |
| 3B  | raspios_oldstable_armhf | 2022-09-06 | 5.10.103| `91e90da69cf0b1ddae23764b417bd6b43ec02c63` |
| 3B  | raspios_oldstable_armhf | 2023-02-21 | 5.10.103| `b57a33ad0991ffc19cd7b47cb7e20e3217705573` |


The following system versions presented issues during the tests:
| RPi |      Image              |  Release   | Kernel  | Issues                           | Firmware Hash   | 
|-----|-------------------------|------------|---------|----------------------------------|-----------------|
| 3B  | raspios_oldstable_armhf | 2022-09-22 | 5.10.103|Camera not detected¹, Screen OFF² | `a1750...9b435` |
| 3B  | raspios_oldstable_armhf | 2023-05-03 | 5.10.103|Uncalibr. touchscreen³, Screen OFF| `638c7...7ea5b` |
| 3B  | raspios_oldstable_armhf | 2023-12-05 | 6.1.21  |Uncalibr. touchscreen             | `446f3...e19da` |


_¹ Camera seems not detected due to a transition from old Camera library to new library. No solution found at the moment. Use another version._  
_² The screen drivers seems to be broken and provoke the screen to turn off. Redownloading/installing the system may fix the issue._  
_³ The touchscreen issue may or may not be related to the kernel version. No solution found at the moment. Use another version._  


> **Note**
> The hash is available in the `.info` file along with the img/xz file, or in the system
> run the command `cat /boot/issue.txt`
