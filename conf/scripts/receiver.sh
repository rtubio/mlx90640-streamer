#!/bin/bash

BLOCKSIZE=2304
PORT=5000

logger "Launching streamer to <localhost:$PORT>, blocksize = $BLOCKSIZE"
gst-launch-1.0 udpsrc blocksize=2304 port=$PORT ! rawvideoparse use-sink-caps=false width=32 height=24 format=rgb framerate=16/1 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480 ! autovideosink
