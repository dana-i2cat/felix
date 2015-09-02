#!/bin/bash

HOST="localhost"
DB_PREFIX="fms__"
DATABASES=("monitoring_topology" "monitoring_sdnrm" "monitoring_serm" "monitoring_crm" "monitoring_tnrm")

if [[ $(dpkg -l | grep mysql-server) != "" ]]; then
    echo "MySQL server already installed. Skipping..."
else
    sudo aptitude -y install mysql-server
fi

## Ask for root and user credentials
while [[ $user_root == "" ]]
    do
        echo ""
        echo "Provide your MySQL root credentials in order to create the Monitoring-server databases"
        read -p "MySQL root user: " user_root
        echo -n Password: 
        read -s password_root
        echo ""
done  
while [[ $user == "" ]]
    do
        echo ""
        echo "Credentials for the user with access the Monitoring-server databases (if doubtful use the previous ones)"
        read -p "User: " user
        echo -n Password: 
        read -s password
        echo ""
done

## Create user if it does not exists
if [[ $(mysql -u $user_root -p$password_root --execute="SELECT * FROM mysql.user WHERE User='$user';") == "" ]]; then
    mysql -u $user_root -p$password_root --execute="CREATE USER '$user'@$HOST IDENTIFIED BY '$password';"
    echo "Creating MySQL user $user@$HOST"
fi

for database in ${DATABASES[@]}
    do
        mysql -u $user_root -p$password_root < $database.sql
        echo "CREATE DATABASE $DB_PREFIX$database"
        mysql -u $user_root -p$password_root --execute="GRANT ALL ON $DB_PREFIX$database.* to $user@$HOST IDENTIFIED BY '$password';"
        echo "Granting privileges on $DB_PREFIX$database to $user@$HOST"
done

echo "MySQL databases successfully created"
