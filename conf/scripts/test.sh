#!/bin/bash
#
# This script executes a test using the MLX90640 installed service.
#
# ricardo[at]karbontek.co.jp

[[ $# -ne 3 ]] && {
  echo "Need to specify the following 3 arguments to call this script:"
  echo "> USER : name of the user in the remote computer where the data is to be copied to"
  echo "> HOST : name of the remote host where the data is to be copied to"
  echo "> MAX  : number of seconds that the test lasts"
  exit -1
}

USER="$1"
HOST="$2"
LOCAL_DATABIN="/tmp/dataset.bin"
REMOTE_DATABIN="~/databin.raw"

left=0
max="$3"     # default time to wait for the test to end

sudo service mlx90640 restart || {
  echo "Could not restart/start the MLX90640 service, please check."
  exit -1
}

echo ">>> Test starts on $(date)"

echo "Countdown until the test ends..."
for counter in $( seq 0 1 $max )
do
  let "left=max-counter"
  echo -n "$left "
  sleep 1
done

echo "Test ended, stopping services and collecting data..."
sudo service mlx90640 stop || {
  echo "Could not stop the MLX90640 service, please check."
  exit -1
}

echo ">>> Test ended on $(date)"

# Simple hack to check if, in case it is a local network name, the name has been resolved
ping -c 5 "$HOST" || ping -c 5 "$HOST"

scp "$LOCAL_DATABIN" $USER@$HOST:"$REMOTE_DATABIN" || {
  echo "Could not copy <$LOCAL_DATABIN> to <$REMOTE_DATABIN> as <$USER> on <$HOST>"
  exit -1
}

echo "Test executed succesffully"
