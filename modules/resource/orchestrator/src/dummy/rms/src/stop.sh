#!/bin/bash

PROC="python main_simulators.py"

#pids=`ps -C "${PROC}" -o pid=`
pids=`ps -eaf | grep "${PROC}" | grep -v "grep" | awk '{ print $2 }'`

echo  "killing: " ${pids}
if [[ "x"${pids} != "x" ]]; then
	kill -9 ${pids}
fi

echo "bye bye..."
exit 1
