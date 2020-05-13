#!/bin/bash

source /etc/streamer.conf

logger "Launching streamer to <$HOST:$PORT> with fps ($FPS)"
/usr/local/bin/mlx90640-streamer $FPS | gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
