#!/bin/bash
#
# This script installs the streamer as a systemd service into the system.
#
# rtpardavila@gmail.com

configure_os () {
  # Configures the operating system to run the streaming binary as a service
  [[ -z $( cat "/etc/passwd" | cut -d':' -f1 | grep "$SERVICE_USER" ) ]] && {
      sudo useradd -s /usr/sbin/nologin -r -m -d "$SERVICE_WORKINGDIR" "$SERVICE_USER"
  } || {
      echo "[$0] User <$SERVICE_USER> exists, skipping..."
  }
}

configure_systemd () {

  sudo cp -f "$STREAMER_PATH" "$STREAMER_BINARY"
	sudo chown "$SERVICE_USER:$SERVICE_USER" "$STREAMER_BINARY"
	sudo chmod ug+x "$STREAMER_BINARY"

  [[ ! -d "$SERVICE_WORKINGDIR" ]] && sudo mkdir -p "$SERVICE_WORKINGDIR"

  create_systemd_conf "$systemd_service_conf" \
    "$SERVICE_EXEC" "$SERVICE_WORKINGDIR" "$SERVICE_ID" "$SYSTEMD_USER" "$SERVICE_PID"\
    "$SERVICE_ID"

  sudo systemctl daemon-reload && \
    sudo systemctl enable "$SERVICE_NAME" && \
    sudo systemctl start "$SERVICE_NAME"

}

create_streamer_conf () {
    # This function creates the configuration file for the streaming script.
    # $1 : path to the configuration file
    # $2 : FPS (default value)
    # $3 : HOST (default value)
    # $4 : PORT (default value)

  [[ -f "$streamer_conf" ]] && {
    echo "[$0] Streamer configuration file <$streamer_conf> exists, skipping..."
    return
  }

  filestr=$"
FPS=$FPS
HOST=$REMOTE_HOST
PORT=$REMOTE_PORT
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

source "conf/project.ini"

configure_os
make pristine && sudo make install
create_streamer_conf
configure_systemd
