#!/bin/bash
#
# Simple countdown script to monitor the time left for a sequential process.
#
# rtpardavila[at]gmail[dot]com

counter="$1"

while [[ $counter -gt 0 ]]
do
  echo -n "$counter "
  ((counter--))
  sleep 1
done
