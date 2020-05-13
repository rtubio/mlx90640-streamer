#!/bin/bash

source "conf/integration.conf"

sudo userdel --force --remove "$SERVICE_USER"

sudo rm -f "$SERVICE_BINARY"
sudo rm -f "$STREAMER_BINARY"
sudo rm -f "$streamer_conf"
sudo rm -f "$systemd_service_conf"

sudo systemctl stop "$SERVICE_ID" && sudo systemctl disable "$SERVICE_ID"
sudo systemctl daemon-reload
