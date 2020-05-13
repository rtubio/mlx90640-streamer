#!/bin/bash
#
# This file sets the right PYTHONPATH (to include XPYTHON) and executes the processor.
# All the command line arguments passed to this script are relayed to the Python processor.
#
# @author : rtpardavila@gmail.com

cleanup () {
  deactivate
}

source "conf/project.ini"

trap cleanup EXIT

# to avoid pushing too many dirs into PYTHONPATH
[[ -z "$( echo $PYTHONPATH |  grep xpython )" ]] && export PYTHONPATH="$PYTHONPATH:$XPYTHON_PATH"
source "$PYENV_ACTIVATE" && python "processor/processor.py" "$*"
