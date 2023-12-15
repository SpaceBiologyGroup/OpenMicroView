#!/bin/bash
# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

SOFT_NAME='OpenMicroView'
INSTALL_DIR="/opt/${SOFT_NAME}"
ENTRYPOINT="${INSTALL_DIR}/start.py"
USERNAME=$(id -nu 1000 || (echo 'pi' && echo 'falling back to "pi" username'>&2))
SYS_USER='root'
SYSTEM_DEP_FILE="install/apt-requirements.list"
PIP_DEP_FILE='install/pip/requirements.txt'
SYSD_FILE="/etc/systemd/system/$SOFT_NAME.service"
opts=$@

COLOR1="\E[38;2;100;180;250m"
OK_COLOR="\E[32m"
ERR_COLOR="\E[31m"
WARN_COLOR="\E[38;2;235;110;0m"
MC="\E[38;2;0;220;255m"
RCOLOR="\033[m"
# Options
DAEMON_INSTALL=0
DEPENDENCIES_INSTALL=0
CONFIG_CHECK=0
SHOW_LICENSE=0

TESTED_OS=(
    "2019-09-26"
    "2021-12-02"
    "2022-01-28"
    "2022-04-04"
    "2022-09-06"
)

no_color(){
    COLOR1=""
    OK_COLOR=""
    ERR_COLOR=""
    WARN_COLOR=""
    MC=""
}

usage(){
echo "Usage: $0 [OPTION]...
Install $SOFT_NAME requirements.

  -h      Show this Help and exit
  -L      Show License and exit

  -A      All: equivalent to '-DSC', recommended for a full install
  -D      Install apt and python Dependencies as root
  -S      Install as a Service, auto-start at boot.
  -C      Check raspberry pi configuration.
  -t      No Colors - if your terminal doesn't support coloring.

Debug:
  In case of error during daemon installation, the following things should be
  checked in the systemd file ($SYSD_FILE):
  - DISPLAY should be the value of \$DISPLAY when checked on the direct screen.
    current \$DISPLAY value : '$DISPLAY'
  - XAuthotity path should exists. Check the username is the main user.
    Default user: uid=1000 ($USERNAME)
  "
  exit 0
}

license(){
    less ./LICENSE
    exit
}

# Relocate to project root directory
install_dir=$(dirname "$0")
cd "${install_dir}/../" 2>/dev/null

# Check options
while getopts "hADStCL" arg; do
  case $arg in
    h) usage ;;
    L) license ;;
    A) DAEMON_INSTALL=1
       DEPENDENCIES_INSTALL=1
       CONFIG_CHECK=1 ;;
    D) DEPENDENCIES_INSTALL=1 ;;
    C) CONFIG_CHECK=1 ;;
    S) DAEMON_INSTALL=1 ;;
    t) no_color ;;
  esac
done

# Formatting
info(){
    msg="$@"
    echo -e $COLOR1 "[INFO]" $msg $RCOLOR
}

ok(){
    msg="$@"
    echo -e $OK_COLOR "[ OK ]" $msg $RCOLOR
}

error(){
    msg="$@"
    echo -e $ERR_COLOR "[ERR ]" $msg $RCOLOR
}

warning(){
    msg="$@"
    echo -e $WARN_COLOR "[WARN]" $msg $RCOLOR
}

# FUNCTIONS
install_sys_deps(){
    info "Updating apt database..."
    apt update
    [[ $? -ne 0 ]] && error "An error occured... Continue ? " && read
    info "Installing system dependencies..."
    xargs apt install -y < $SYSTEM_DEP_FILE
    [[ $? -ne 0 ]] && error "An error occured... Continue ? " && read
    ok "System dependencies installed."
}

install_python_deps(){
    info "Installing python dependencies..."
    /usr/bin/python3 -m pip install -r $PIP_DEP_FILE
    ok "Python dependencies installed."
}

# daemon installation
setup_permissions(){
    chown $SYS_USER:$SYS_USER -R $INSTALL_DIR &&
	chmod 600 $INSTALL_DIR/*.py &&
	chmod 700 $ENTRYPOINT ||
	(error "An error occured while setting up permissions. Continue anyway ? " && read)
}

install_autostart(){
    info "Installing $SOFT_NAME in ${INSTALL_DIR}..."
    mkdir -p $INSTALL_DIR
    cp -R ./src ./start.py $INSTALL_DIR
    echo "$SERVICE_FILE" > $SYSD_FILE
    systemctl daemon-reload
    systemctl enable $SOFT_NAME.service
    ok "Service as been enable at boot."
    info "To disable autoboot, use: '${RCOLOR}systemctl disable $SOFT_NAME.service${COLOR1}'"
    info "To manually start $SOFT_NAME, use: '${RCOLOR}service $SOFT_NAME start${COLOR1}'"
}

# MAIN :

BANNER="$COLOR1
  ______   .______    _______ .__   __.  ${MC}.__.  .__.  ${COLOR1}____    ____  __   _______ ____    __    ____
 /  __  \  |   _  \  |   ____||  \ |  |  ${MC}|::|  |::|  ${COLOR1}\   \  /   / |  | |   ____|\   \  /  \  /   /
|  |  |  | |  |_)  | |  |__   |   \|  |  ${MC}|::|  |::|  ${COLOR1} \   \/   /  |  | |  |__    \   \/    \/   /
|  |  |  | |   ___/  |   __|  |  . '  |  ${MC}|::╰──╯::| ${COLOR1}   \      /   |  | |   __|    \            /
|  '--'  | |  |      |  |____ |  |\   |  ${MC}|::::::::\_${COLOR1}    \    /    |  | |  |____    \    /\    /
 \______/  | _|      |_______||__| \__|  ${MC}|::|‾‾‾‾'::'${COLOR1}    \__/     |__| |_______|    \__/  \__/
                                         ${MC}|::|
                                         ${MC}|::|$ERR_COLOR           _ _  _ ____ ___ ____ _    _    ____ ____
                                         ${MC}|,-'$ERR_COLOR           | |\ | [__   |  |__| |    |    |___ |__/
                                         ${MC}    $ERR_COLOR           | | \| ___]  |  |  | |___ |___ |___ |  \\
$RCOLOR
OpenMicroView - Copyright (C) 2023 V. Salvadori
 This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are welcome to
 redistribute it under certain conditions.
 For details read the complete LICENSE file with '$0 -L'.
"
echo -e "$BANNER"

#  Check if User is root
if [[ $UID -ne 0 ]]; then
    error "Installation should be run as root."
    exit
fi

#  Check location is correct
if [ ! -d "./install" ]; then
    error "Script should be started from project's root directory. (current: $(pwd))"
    exit
fi

CHOICE=$(( DEPENDENCIES_INSTALL + DAEMON_INSTALL + CONFIG_CHECK ))
if [[ "$CHOICE" -eq 0 ]]; then
    error "No option was chosen."
    echo
    usage
fi

#  Check Display is set in case daemon install is set
if [[ "$DAEMON_INSTALL" -eq 1 ]] && [[ ! $DISPLAY ]]; then
    warning "DISPLAY is not set."
    echo -e "${WARN_COLOR} > Press ${OK_COLOR}ENTER${WARN_COLOR} to use default ':0' or start install script from pi display (use ${ERR_COLOR}CTRL+C${WARN_COLOR} to cancel installation).$RCOLOR"
    read -p 'Continue ?'
    DISPLAY=':0.0'
fi

sleep 1
# Normal installation
if [[ $DEPENDENCIES_INSTALL -eq 1 ]]; then
    install_sys_deps
    install_python_deps
    ok "Dependencies Installation complete."
fi

# Daemon install
SERVICE_FILE="\
[Unit]
Description=$SOFT_NAME service
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
Environment=\"DISPLAY=$DISPLAY\"
Environment=\"XAUTHORITY=/home/$USERNAME/.Xauthority\"
Restart=on-failure
RestartSec=3
User=$SYS_USER
ExecStart=/usr/bin/python3 $ENTRYPOINT

[Install]
WantedBy=graphical.target"


if [[ DAEMON_INSTALL -eq 1 ]]; then
    install_autostart
    setup_permissions
    ok "Service Installation complete."
fi

# Config Check

check_versions(){
    release=$(egrep -o "20[0-9]{2}-[0-1][0-9]-[0-3][0-9]" /boot/issue.txt)
    for version in ${TESTED_OS[@]}; do
        if [[ "${version}" == "${release}" ]]; then
            ok "OS Version ${release} has been tested and validated"
            return 1
        fi
    done
    warning "OS Version ${release} has not been tested or validated. Full Version:"
    cat /boot/issue.txt
    return 0
}

is_set(){
        search_text=$1
	file=$2
        grep $search_text $file >/dev/null
        return $?
}

check(){
    param=$1
    return_code=$2
    level=$3
    error=$4
	file=$5
	full_line=$6
	[[ $full_line -eq 0 ]] && RE="$param" || RE="^$param\$"
    is_set $RE $file
    r=$?
    if [[ $r -ne $return_code ]]; then
    [[ $return_code -eq 0 ]] && t="not set" || t="is a misconfiguration"
            $level "$file: '$param' $t, $error"
	else
    [[ $return_code -ne 0 ]] && t="error absent" || t="is set"
            ok "$file: '$param' $t"
    fi
    return $r
}


if [[ CONFIG_CHECK -eq 1 ]]; then
    check_versions
	boot_config='/boot/config.txt'
	info "Checking '$boot_config'..."
	check "dtparam=audio=off" 0 error "LED may not work properly. Edit $boot_config manually" $boot_config 1
    if [[ $? -ne 0 ]]; then
        line=$(grep 'dtparam=audio=' $boot_config -n)
        if [[ $? -eq 0 ]]; then
            warning "dtparam config is present on line $line"
        fi
    fi
	check "start_x=1" 0 error "Camera seems disable. Use 'sudo raspi-config' > 3 > 1 > Yes" $boot_config 1
	check "gpu_mem=128" 0 warning "gpu_mem should be >= 128 for the camera to work properly" $boot_config 1
	# check "enable_uart=1" 0 info "required for non-root operation" $boot_config
	# check "dtparam=spi=on" 0 info "required for non-root operation" $boot_config
	info "Checking Service configuration..."
	ls -l $SYSD_FILE >/dev/null 2>/dev/null
	if [[ $? -ne 0 ]]; then
		info "$SOFT_NAME Service is not installed."
	else
		ok "$SOFT_NAME Service is installed."
		check 'DISPLAY="' 1 error 'DISPLAY should be set to something (usually :0 or :0.0)' $SYSD_FILE 0
		xa_file=$(grep -o '/home/\w*/.Xauthority' /etc/systemd/system/OpenMicroView.service)
		if [[ ! -f $xa_file ]]; then
	                error "$SYSD_FILE: XAUTHORITY path is incorrect, '$xa_file' not found "
		else
	                ok "$SYSD_FILE: XAUTHORITY path seems correct"
		fi
	fi
    if [[ -f '/var/run/reboot-required' ]]; then
        warning "Reboot is required to complete installation."
    else
        info "Reboot may be required if you edited the configuration."
    fi
fi

