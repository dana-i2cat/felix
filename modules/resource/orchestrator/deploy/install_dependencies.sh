#!/bin/sh

echo "Installing RO manageDB dependencies..."

SUDO=`which sudo`
$SUDO apt-get install -y python-pip mongodb-server

PIP=`which pip`
$SUDO $PIP install -r pip_dependencies

echo "Installing RO manageDB dependencies... Done"
