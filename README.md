[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Static Badge](https://img.shields.io/badge/Platform-Raspberry%20Pi-red?logo=raspberrypi)

# _OpenµView_
## Description
OpenµView is a project of open source microscope. Both the hardware and the software
are available to most. The total costs for the Hardware is about ~250 USD, including
the 3D printed parts, and the electronic pieces. OpenMicroView is running on a
RaspberryPi micro computer (see [tested hardware](#hardware)). All details are made
available in the published article (available soon).

# Installation and Configuration
## Prerequisite
Before to continue with the software installation, make sure you've built the microscope
hardware.

You'll need a Micro-SD Card with a fresh system (see below, [tested versions](#operating-system)), 
we recommend you to flash the SD Card using the Raspberry Pi Imager.  
Insert it in your Raspberry Pi (see below [tested hardware](#hardware)).  

_Network and user configurations are not covered here as it depends on your setup. 
During our tests the default user was used, and the connection to the network
was established via cable._

## Installation of OpenMicroView
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
```sh
sudo OpenMicroView/install/install.sh -D
```

### 3. Installing as Service
```sh
sudo OpenMicroView/install/install.sh -S
```
The software will be copied in `/opt/OpenMicroView/` and a service file
will be created in the systemd directory.

### 4. Check your raspberry pi configuration
The install script allows you to check for classical configuration errors,
To do so you can just run the following command as root:
```sh
sudo OpenMicroView/install/install.sh -C
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
sudo OpenMicroView/install/install.sh -E
```
then, run step `4.` Once again to check the final config.

### 6. Reboot
Reboot the system (`sudo reboot`). Then, OpenMicroView UI should show up at start.

### Note
You can see full usage of the installation tool using:
```sh
install/install.sh -h
```

## Raspberry Pi Configuration
This part of the Raspberry Pi configuration is covered by the installer above when 
using the `-E` or `-A` options. 

Nevertheless, the Camera can be manually activated using `raspi-config`:
 - `3 Interface Options` > `1 Camera` > `Yes`   

That will automatically add the following lines at the end of `/boot/config.txt`
```toml
[all]
start_x=1
gpu_mem=128
```

You can also manually edit the same config file to allow LEDs to work correctly:
```conf
dtparam=audio=off
```

#### Allow software to run as normal user
While this is theoritically feasable, this procedure **has not been tested** and
is therefore not recommended.  
To allow the software to run as normal user the following change would be required:
- Connect LED to D10 instead of D18 GPIO PIN
- In file `src/open_micro_view/microscope_light.py`, change constant `LED_PIN` 
  to `board.D10`
- In `/boot/config.txt` verify/change or add the config:
  ```conf
  dtparam=spi=on
  enable_uart=1
  ```

> **Note**  
> Running the process as a normal user may provoke permission errors while
> saving, reading or copying pictures. The setup of directory permissions are
> not detailled here.


# Starting the interface
## Service
If you installed OpenMicroView as a Service, you can restart the system
or use the following commands to start/stop/restart or view the status
of OpenMicroView:
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
journalctl -u OpenMicroView -f
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

# Usage
After reboot, the GUI will automatically start on the OpenMicroView 
Microscope Screen.In the main view, you can preview the camera capture
and you will have access to light, camera and Timelapse settings. 
You can change light color and brigthness and adjust camera contrast,
brightness and saturation. On the bottom of the view, you can see the
current temperature and framerate. If the temperature reached is too
high, the raspberry may shutdown automatically. You also see the 
resolution of the next picture to be taken.

In the Timelapse Section you can set several parameters such as the interval
of pictures in the timelapse, or the quantity of frames to be taken. When 
capturing over long timeframe do not forget to lock the camera sensor and 
lens position, using the physical lockers, to prevent shifting.

In the settings you can adjust the resolution of the pictures taken,
save or load light/camera configuration for later use. Picture management
is also possible : you can copy all pictures to a USB storage, browse
local pictures or delete all pictures. A button allows you to switch off
or reboot the Raspberry Pi, directly from the GUI.

The picture browser allows you to view existing pictures and timelapses.
Timelapses can be previewed and played, but the loading can take some time,
depending on the size of it. Each Picture or timelapse can be deleted.

# Debugging
- `Authentication error`:
  - Make sure you are logged in as root or you prepended `sudo`
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

# License
 OpenMicroView - Copyright © 2023   
 This program comes with ABSOLUTELY NO WARRANTY.   
 This is free software, and you are welcome to redistribute it
 under certain conditions.  
 See [license file](LICENSE) for more details
