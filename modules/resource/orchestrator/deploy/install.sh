#!/bin/sh

echo "Installing Resource Orchestrator..."

# Installing RO dependencies
./install_dependencies.sh

# Configuring database with a dummy entry
dbmanage_path="../src/admin/db"
python $dbmanage_path/manage.py add_route_entry -t "virtualisation" -a 127.0.0.1 -p 8445 --protocol "https" --endpoint "xmlrpc/plugin/" --user "dummy" --password "dummy"

echo "Installing Resource Orchestrator... Done"
