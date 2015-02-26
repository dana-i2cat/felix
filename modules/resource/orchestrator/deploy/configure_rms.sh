#!/bin/bash

echo "Configuring Resource Orchestrator..."

clean=${clean:-'no'}
dummy=${dummy:-'no'}

# Specify proper values here, if needed
proto=${proto:-'https'}
endpoint=${endpoint:-'xmlrpc/geni/3/'}
user=${user:-""}
pswd=${pswd:-""}

# Configuring database with a dummy entry
dbmanage_path="../src/admin/db"

config_entry() {
    echo -n "Please enter $1 IP address: "
    read ip
    echo -n "Please enter $1 PORT number: "
    read port

    python manage.py add_route_entry -t $1 -a $ip -p $port --protocol $proto --endpoint $endpoint
}

# Clean the environment
if [[ $clean != "no" ]]; then
    echo "Delete all tables..."
    python $dbmanage_path/action_db.py --action "delete_all_tables"
fi

# Fill the database with dummy entries (if required)
cd $dbmanage_path
if [[ $dummy != "no" ]]; then
    echo "Filling database with dummy entries..."
    ./dummy_install.sh
    echo "Filling database with dummy entries... Done"
else
    echo "Filling database with config entries..."
    while true; do
        echo
        echo -n "Choose the RM to configure [c,sdn,se,tn,ro] (any other to quit): "
        read x

        if [[ x$x == x"c" ]]; then
            config_entry "virtualisation"
        elif [[ x$x == x"sdn" ]]; then
            config_entry "sdn_networking"
        elif [[ x$x == x"se" ]]; then
            config_entry "stitching_entity"
        elif [[ x$x == x"tn" ]]; then
            config_entry "transport_network"
        elif [[ x$x == x"ro" ]]; then
            config_entry "island_ro"
        else
            break
        fi
    done
    echo "Filling database with config entries... Done"
fi
cd - >/dev/null

echo "Configuring Resource Orchestrator... Done"
