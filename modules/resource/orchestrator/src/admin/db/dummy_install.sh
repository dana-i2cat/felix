#!/bin/bash

host_ip="127.0.0.1"
endpoint="xmlrpc/geni/3/"
user=""
password=""

# XXX WARNING: this removes everything in the RoutingDatabase!

echo "Current database information..."

python manage.py dump

echo "Removing database from current RMs..."

python manage.py delete_route_entry -a $host_ip --endpoint "$endpoint"


echo "Filling database with dummy RMs..."

python manage.py add_route_entry -t "virtualisation" -a $host_ip -p 8445 --protocol "https" --endpoint "$endpoint" --user "" --password ""

python manage.py add_route_entry -t "sdn_networking" -a $host_ip -p 8443 --protocol "https" --endpoint "$endpoint" --user "" --password ""

#python manage.py add_route_entry -t "transport_network" -a $host_ip -p 18446 --protocol "https" --endpoint "$endpoint" --user "" --password ""

#python manage.py add_route_entry -t "stitching_entity" -a $host_ip -p 18447 --protocol "https" --endpoint "$endpoint" --user "" --password ""

