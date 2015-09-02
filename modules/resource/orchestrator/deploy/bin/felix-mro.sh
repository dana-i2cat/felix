#!/bin/sh

## Daemonizer for the FELIX Resource Orchestrator.
## Expected to work under both Debian-based systems and RedHat.
## Version: 0.1
## Author: Carolina Fernandez
## Organization: i2CAT

# chkconfig: 2345 80 20
# processname: felix-mro
# description: startup script for FELIX Resource Orchestrator

### BEGIN INIT INFO
# Provides: felix-mro
# Required-Start: $local_fs $remote_fs $network $syslog
# Required-Stop: $local_fs $remote_fs $network $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: startup script for FELIX Resource Orchestrator
### END INIT INFO
#


# Name for the service, used in logging
FELIX_RO_NAME=felix-mro

# Title for the service, used in service commands
FELIX_RO_TITLE="FELIX Resource Master Orchestrator"

# Name of the user to be used to execute the service
FELIX_RO_USER=root
#FELIX_RO_USER=i2cat

# In which directory is the shell script that this service will execute
FELIX_RO_HOME=/opt/felix/resource-orchestrator-mro/modules/resource/orchestrator

# Where to write the process identifier - this is used to track if the service is already running 
# Note: the script noted in the COMMAND must actually write this file 
PID_FILE=/var/run/$FELIX_RO_NAME.pid

# File to handle instances of the program
LOCK_FILE=/var/lock/$FELIX_RO_NAME

# Where to write the contents
LOG_FOLDER=$FELIX_RO_HOME/log
LOG_FILE=$LOG_FOLDER/resource-orchestrator.log

## Where to write the init script log file (check start, stop, etc)
#LOG_INITSCRIPT_FILE=$LOG_FOLDER/access.log

# How can the script be identified if it appears in a 'ps' command via grep? 
# Examples to use are 'java', 'python' etc.
PROCESS_TYPE=/usr/bin/python

# Construct the command(s) to invoke the proper script(s)
EXEC="$PROCESS_TYPE $FELIX_RO_HOME/src/main.py"

# Return variables
RET_SUCCESS=0
RET_FAILURE=1

export FELIX_RO_HOME

if [ -e /etc/redhat-release ]; then
  . /etc/init.d/functions
fi

# Is the service already running? If so, capture the process id 
if [ -f $PID_FILE ]; then
  PID=`cat $PID_FILE`
else
  PID=""
fi

create_log() {
  # Create symlink to log within Resource Orchestrator if not previously there
  if [ ! -L /var/log/$FELIX_RO_NAME ]; then
   ln -sf $LOG_FOLDER/ /var/log/$FELIX_RO_NAME
  fi
}

do_start()
{
  # Return
  #  0 if daemon has been started
  #  1 if daemon was already running
  #  2 if daemon could not be started
  start-stop-daemon --start --quiet -b --pidfile $PID_FILE --exec $EXEC --test > /dev/null \
    || return 1
  start-stop-daemon --start --quiet -b -m --pidfile $PID_FILE --exec $EXEC -- \
    || return 2
  # Add code here, if necessary, that waits for the process to be ready
  # to handle requests from services started subsequently which depend
  # on this one.  As a last resort, sleep for some time.
}

do_stop()
{
  # Return
  #  0 if daemon has been stopped
  #  1 if daemon was already stopped
  #  2 if daemon could not be stopped
  #  other if a failure occurred
  start-stop-daemon --stop --quiet --retry=TERM/3/KILL/5 --pidfile $PID_FILE --pidfile $PID_FILE
  RETVAL="$?"
  [ "$RETVAL" = 2 ] && return 2
  # Wait for children to finish too if this is a daemon that forks
  # and if the daemon is only ever run from this initscript.
  # If the above conditions are not satisfied then add some other code
  # that waits for the process to drop all resources that could be
  # needed by services started subsequently.  A last resort is to
  # sleep for some time.
  start-stop-daemon --stop --quiet --oknodo --retry=0/3/KILL/5 --exec $EXEC --pidfile $PID_FILE
  [ "$?" = 2 ] && return 2
  # Many daemons don't delete their pidfiles when they exit.
  rm -f $PID_FILE

  # Kill the other process
  ro_p_id=`ps ax | grep "resource-orchestrator-mro" | grep "main.py" | grep -v "grep" | awk '{print $1}'`
  [ "$ro_p_id" != "" ] && kill -s KILL $ro_p_id || :
  return "$RETVAL"
}

do_restart() {
  do_stop
  sleep 1
  do_start
}

do_force_reload() {
  backup_domain_peers_path=/tmp/${FELIX_RO_NAME}_peers_dump
  # Do a backup of the domain peers
  mongodump --collection domain.routing --db felix_mro --out $backup_domain_peers_path
  mongo < $FELIX_RO_HOME/deploy/bin/clean_db/drop_mro_db.js
  # Restore backup of the domain peers
  mongorestore $backup_domain_peers_path
  rm -rf $backup_domain_peers_path
}

do_check_status() {
  if [ "$PID" != "" ]; then
   STATUS="running (pid $PID)"
  else
   STATUS="NOT running"
  fi
  echo "$FELIX_RO_TITLE is $STATUS."
}

case "$1" in
  start)
    action="Starting $FELIX_RO_TITLE.";
    echo $action;
    do_start;
    exit $?
  ;;
  stop)
    action="Stopping $FELIX_RO_TITLE.";
    echo $action;
    do_stop;
    exit $?
  ;;
  restart)
    action="Restarting $FELIX_RO_TITLE.";
    echo $action;
    do_restart;
    exit $?
  ;;
  status)
    do_check_status;
    exit $?
  ;;
  force-reload)
    action="Cleaning internal database and restarting $FELIX_RO_TITLE.";
    echo $action;
    do_stop;
    do_force_reload;
    do_start;
    exit $?
  ;;   
  *)
    echo "Usage: service $FELIX_RO_NAME {start|stop|restart|force-reload|status}";
    exit $RET_SUCCESS
  ;;
esac
