#!/bin/bash

echo "Installing Resource Orchestrator..."

# Installing RO dependencies
./install_dependencies.sh

# Link init script to /etc/init.d
if [[ ! -L /etc/init.d/felix-ro ]]; then
  echo "Creating symlink..."
  sudo ln -s $PWD/bin/felix-ro.sh /etc/init.d/felix-ro
  echo "Creating symlink... Done"
fi

echo "Installing Resource Orchestrator... Done"
