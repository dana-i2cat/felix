#!/bin/bash

echo "Installing Resource Orchestrator..."

# Installing RO dependencies
./install_dependencies.sh

# Link init scripts to /etc/init.d
if [[ ! -L /etc/init.d/felix-ro ]]; then
  echo "Creating symlink for RO..."
  sudo ln -s $PWD/bin/felix-ro.sh /etc/init.d/felix-ro
  echo "Creating symlink for RO... Done"
fi

if [[ ! -L /etc/init.d/felix-mro ]]; then
  echo "Creating symlink for MRO..."
  sudo ln -s $PWD/bin/felix-mro.sh /etc/init.d/felix-mro
  echo "Creating symlink for MRO... Done"
fi

echo "Installing Resource Orchestrator... Done"
