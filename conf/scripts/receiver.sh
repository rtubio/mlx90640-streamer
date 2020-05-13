#!/bin/bash

DATALOG=/tmp/datalog.bin
BLOCKSIZE=2304
PORT_RX=5000
PORT_FORWARD=5001

logger "Launching streamer to <localhost:$PORT>, blocksize = $BLOCKSIZE"

# nc -lp "$PORT" | tee "$DATALOG" | nc localhost "$PORT_FORWARD"
nc -ulp $PORT_RX | tee "$DATALOG" | socat stdin udp:127.0.0.1:$PORT_FORWARD &

gst-launch-1.0 udpsrc blocksize=2304 port=$PORT_FORWARD ! rawvideoparse use-sink-caps=false width=32 height=24 format=rgb framerate=16/1 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480 ! autovideosink
