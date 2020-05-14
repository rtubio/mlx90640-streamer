#!/bin/bash

source /etc/streamer.conf

logger "Launching streamer to <$HOST:$PORT> with fps ($FPS)"

[[ -z "$DEBUG" ]] && {
  /usr/local/bin/mlx90640-streamer $FPS "debug" | \
    gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
} || {
  /usr/local/bin/mlx90640-streamer $FPS | \
    gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
}
