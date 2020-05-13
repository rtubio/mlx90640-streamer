#!/bin/bash

PORT=5000

logger "Launching streamer to <localhost:$PORT>"
gst-launch-1.0 udpsrc blocksize=2304 port=$PORT ! rawvideoparse use-sink-caps=false width=32 height=24 format=rgb framerate=16/1 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480 ! autovideosink
