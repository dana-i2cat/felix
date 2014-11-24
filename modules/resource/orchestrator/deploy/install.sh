#!/bin/bash

echo "Installing Resource Orchestrator..."

clean=${clean:-'no'}
ip=${ip:-'127.0.0.1'}
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

if [[ $clean != "no" ]]; then
    echo "Delete all tables..."
    python $dbmanage_path/action_db.py --action "delete_all_tables"
fi

# Fill with data only when database is empty
db_content=$(python $dbmanage_path/manage.py dump | wc -l)
db_lines_to_show=$(($db_content-2))
if [[ $(python $dbmanage_path/manage.py dump | tail -$db_lines_to_show) == "" ]]; then
  echo "Filling database..."
  $dbmanage_path/dummy_install.sh
  echo "Filling database... Done"
fi

echo "Installing Resource Orchestrator... Done"
