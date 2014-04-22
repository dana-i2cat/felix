#!/bin/sh

echo "install RO manageDB dependencies"

SUDO=`which sudo`
$SUDO apt-get install -y python-pip mongodb-server

PIP=`which pip`
$SUDO $PIP install argparse pymongo

echo "install RO manageDB dependencies... done"
