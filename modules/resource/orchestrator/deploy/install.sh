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

# Configuring database with a dummy entry
dbmanage_path="../src/admin/db"

# Fill with data only when database is empty
db_content=$(python $dbmanage_path/manage.py dump | wc -l)
db_lines_to_show=$(($db_content-2))
if [[ $(python $dbmanage_path/manage.py dump | tail -$db_lines_to_show) == "" ]]; then
  echo "Filling database..."
  python $dbmanage_path/manage.py add_route_entry -t "virtualisation" -a 127.0.0.1 -p 8445 --protocol "https" --endpoint "xmlrpc/sfa/" --user "dummy" --password "dummy"
  python $dbmanage_path/manage.py add_route_entry -t "sdn_networking" -a 127.0.0.1 -p 8443 --protocol "https" --endpoint "xmlrpc/sfa/" --user "dummy" --password "dummy"
  echo "Filling database... Done"
fi

echo "Installing Resource Orchestrator... Done"
