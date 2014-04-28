#!/bin/sh

echo "Installing RO manageDB dependencies..."

SUDO=`which sudo`
PCKs='python-pip mongodb-server python-lxml python-m2crypto'
$SUDO apt-get install -y ${PCKs}

PIP=`which pip`
$SUDO $PIP install -r pip_dependencies

echo "Installing RO manageDB dependencies... Done"
