#!/bin/sh

echo "Installing SERM dependencies..."

SUDO=`which sudo`
APT="python-yaml"
$SUDO apt-get install -y ${APT}

PIP=`which pip`
$SUDO $PIP install -r pip_dependencies

echo "Installing SERM dependencies... Done"
