#!/bin/bash
#
# This script installs the streamer as a systemd service into the system.
#
# rtpardavila@gmail.com

load_conf () {
  CONF="conf/project.ini"
  [[ ! -f "$CONF" ]] && {
    echo "[error, $0] Could not find essential <$CONF> file, exiting..."
    exit -1
  }
  source "$CONF"
  USER="$( whoami )"
  echo "[info, $0] Starting execution, pwd = $(pwd)"
}

configure_os () {
  # Configures the operating system to run the streaming binary as a service
  [[ -z $( cat "/etc/passwd" | cut -d':' -f1 | grep "$SERVICE_USER" ) ]] && {
    sudo useradd -s /usr/sbin/nologin -r -m -d "$SERVICE_WORKINGDIR" "$SERVICE_USER"
  } || {
    echo "[warn, $0] User <$SERVICE_USER> exists, skipping"
  }

  [[ -z $( uname -a | grep 'Debian' ) ]] && {
    echo "[warn, $0] OS is not Debian, skipping package installation"
    return
  }

  [[ -f "$DEB_PKGS" ]] && {
    sudo apt install $(grep -vE "^\s*#" $DEB_PKGS  | tr "\n" " ")
  } || {
    echo "[warn, $0] OS packages file <$DEB_PKGS> does not exist, skipping"
  }

  [[ -f "$XPYTHON_DEB_PKGS" ]] && {
    sudo apt install $(grep -vE "^\s*#" $XPYTHON_DEB_PKGS  | tr "\n" " ")
  } || {
    echo "[warn, $0] OS packages file <$XPYTHON_DEB_PKGS> does not exist, skipping"
  }

}

setup_pyenv () {
  # Setup of the Python environment
  [[ -z $( uname -a | grep 'Debian' ) ]] && {
    echo "[warn, $0] OS is not Debian, skipping PIP package installation"
    return
  }

  echo "[$0, INF] \"$PYENV_D\" setting up..."
  [[ ! -d "$PYENV_D" ]] && virtualenv --python=python3 "$PYENV_D" &&\
    echo "[$0, INF] \"$PYENV_D\" initialized"
  [[ -f "$PIP_PKGS" ]] && {
    source "$PYENV_ACTIVATE"
    pip install -r "$PIP_PKGS"
    deactivate
  } || {
    echo "[$0, WRN] No \"$PIP_PKGS\" available, skipping PYENV packages installation"
  }

  echo "[$0, INF] \"$PYENV_D\" setting up with xpython packages"
  [[ -f "$XPYTHON_PIP_PKGS" ]] && {
    source "$PYENV_ACTIVATE"
    pip install -r "$XPYTHON_PIP_PKGS"
    deactivate
  } || {
    echo "[$0, WRN] No \"$XPYTHON_PIP_PKGS\" available, skipping PYENV packages installation"
  }

  chmod +x "$freeze_sh"
  ln -sf "$freeze_sh" "$freeze_ln"

}

configure_systemd () {

  sudo cp -f "$STREAMER_PATH" "$STREAMER_BINARY"
	sudo chown "$SERVICE_USER:$SERVICE_USER" "$STREAMER_BINARY"
	sudo chmod ug+x "$STREAMER_BINARY"

  create_systemd_conf "$systemd_service_conf" \
    "$SERVICE_EXEC" "$SERVICE_WORKINGDIR" "$SERVICE_ID" "$SYSTEMD_USER" "$SERVICE_PID"\
    "$SERVICE_ID"

  sudo systemctl daemon-reload && \
    sudo systemctl enable "$SERVICE_NAME" && \
    sudo systemctl start "$SERVICE_NAME"

  sudo service "$SERVICE_ID" restart

}

create_streamer_conf () {
    # This function creates the configuration file for the streaming script.
    # $1 : path to the configuration file
    # $2 : FPS (default value)
    # $3 : HOST (default value)
    # $4 : PORT (default value)

  filestr=$"
FPS=$FPS
HOST=$REMOTE_HOST
PORT=$REMOTE_PORT
DATASETBIN='/tmp/dataset.bin'
DEBUG=0
    "

  echo "$filestr" | sudo tee "$streamer_conf"

}

create_systemd_conf () {
    # This function creates the configuration file for the systemd service, with the latest
    # configuration read from "conf/integration.conf"
    # $1 : path to the configuration file
    # $2 : execution command
    # $3 : working directory for the daemon (path)
    # $4 : service identifier
    # $5 : user to run the deamon as (has the same individual group associated to)
    # $6 : daemon's PID file
    # $7 : working directory name for the daemon

  filestr=$"
[Unit]
Description=MLX90640 streaming service
After=network.target

[Service]
ExecStart=$2
WorkingDirectory=$3
StandardOutput=inherited
StandardError=syslog
SyslogIdentifier=$4
Restart=always
User=$5
Group=$5
PIDFile=$6
PermissionsStartOnly=true
RuntimeDirectory=$7
RuntimeDirectoryMode=0777

[Install]
WantedBy=multi-user.target
  "

  echo "$filestr" | sudo tee "$1"

}

# #####################################################################################################
# ### MAIN LOOP

load_conf
configure_os
setup_pyenv
make pristine && sudo make install
create_streamer_conf
configure_systemd
