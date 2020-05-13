#!/bin/bash

DATALOG=/tmp/dataset.bin
BLOCKSIZE=2304
PORT_RX=5000
PORT_FORWARD=5001

cleanup () {
  # before exiting, let's kill nc running in the background
  jobs
  kill -9 $!
}

logger "Launching streamer to <localhost:$PORT>, blocksize = $BLOCKSIZE"
trap cleanup EXIT   # register the cleanup function to be called on the EXIT signal

[[ -f "$DATALOG" ]] && rm -f "$DATALOG"

nc -ulp $PORT_RX | tee "$DATALOG" | socat stdin udp:127.0.0.1:$PORT_FORWARD &

gst-launch-1.0 udpsrc blocksize=2304 port=$PORT_FORWARD ! rawvideoparse use-sink-caps=false width=32 height=24 format=rgb framerate=16/1 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480 ! autovideosink
