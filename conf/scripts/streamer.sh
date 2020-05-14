#!/bin/bash

source /etc/streamer.conf

logger "[info, $0] Launching streamer to <$HOST:$PORT> with fps ($FPS)"

[[ -f "$DATASETBIN" ]] && rm -f "$DATASETBIN" && logger "[warn, $0] <$DATASETBIN> removed"

[[ -z "$DEBUG" ]] && {
  /usr/local/bin/mlx90640-streamer $FPS "debug" | \
    gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
} || {
  /usr/local/bin/mlx90640-streamer $FPS | \
    gst-launch-1.0 fdsrc blocksize=2304 ! udpsink host=$HOST port=$PORT
}
