#!/bin/bash

source /etc/streamer.conf

logger "[info, $0] Launching streamer to <$HOST:$PORT> with fps ($FPS)"

[[ -f "$DATASETBIN" ]] && rm -f "$DATASETBIN" && logger "[warn, $0] <$DATASETBIN> removed"

# /usr/local/bin/mlx90640-streamer $FPS "2>$DATASETBIN" | \
#  gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT

/usr/local/bin/rawrgb $FPS 2>"$DATASETBIN" | gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
