#!/bin/bash

COMRMGENI3="comrmgeni3"
SDNRMGENI3="sdnrmgeni3"
SERMGENI3="sermgeni3"
TNRMGENI3="tnrmgeni3"
MONITORING="monitoring"

interval=5

function clean() {
    rm -f plugins/${COMRMGENI3}
    rm -f plugins/${SDNRMGENI3}
    rm -f plugins/${SERMGENI3}
    rm -f plugins/${TNRMGENI3}
    rm -f plugins/${MONITORING}
}

function link() {
    cd plugins
    ln -s ../vendor/${1} ${1}
    cd -
}

function run() {
    python main_simulators.py &
}

function simulate() {
    clean
    link ${1}
    run
    sleep $interval
}

simulate ${COMRMGENI3}
simulate ${SDNRMGENI3}
simulate ${SERMGENI3}
simulate ${TNRMGENI3}
simulate ${MONITORING}

echo "bye bye..."
exit 1
