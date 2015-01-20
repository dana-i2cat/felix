#!/bin/bash

echo "Installing Stitching Entity Resource Manager..."

clean=${clean:-'no'}
ip=${ip:-'127.0.0.1'}
# Installing SERM dependencies
./install_dependencies.sh

# Link init script to /etc/init.d
if [[ ! -L /etc/init.d/felix-serm ]]; then
  echo "Creating symlink..."
  sudo ln -s $PWD/bin/felix-serm.sh /etc/init.d/felix-serm
  echo "Creating symlink... Done"
fi

echo "Installing Stitching Entity Resource Manager... Done"
