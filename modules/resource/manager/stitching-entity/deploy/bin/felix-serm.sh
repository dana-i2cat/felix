#!/bin/sh

## Daemonizer for the FELIX Stitching Entity Resource Manager.
## Version: 0.1
## Author: Carolina Fernandez
## Organization: i2CAT

# chkconfig: 2345 80 20
# processname: felix-serm
# description: startup script for FELIX Stitching Entity Resource Manager

### BEGIN INIT INFO
# Provides: felix-serm
# Required-Start: $local_fs $remote_fs $network $syslog
# Required-Stop: $local_fs $remote_fs $network $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: startup script for FELIX Stitching Entity Resource Manager
### END INIT INFO
#


# Name for the service, used in logging
FELIX_SE_NAME=felix-serm

# Title for the service, used in service commands
FELIX_SE_TITLE="FELIX Stitching Entity Resource Manager"

# Name of the user to be used to execute the service
FELIX_SE_USER=root
#FELIX_SE_USER=i2cat

# In which directory is the shell script that this service will execute
FELIX_SE_HOME=/opt/felix/stitching-entity/modules/resource/manager/stitching-entity

# Where to write the process identifier - this is used to track if the service is already running 
# Note: the script noted in the COMMAND must actually write this file 
PID_FILE=/var/run/$FELIX_SE_NAME.pid

# File to handle instances of the program
LOCK_FILE=/var/lock/$FELIX_SE_NAME

# Where to write the contents
LOG_FOLDER=$FELIX_SE_HOME/log
LOG_FILE=$LOG_FOLDER/stitching-entity.log

## Where to write the init script log file (check start, stop, etc)
#LOG_INITSCRIPT_FILE=$LOG_FOLDER/access.log

# How can the script be identified if it appears in a 'ps' command via grep? 
# Examples to use are 'java', 'python' etc.
PROCESS_TYPE=/usr/bin/python

# Construct the command(s) to invoke the proper script(s)
EXEC="$PROCESS_TYPE $FELIX_SE_HOME/src/main.py"

# Return variables
RET_SUCCESS=0
RET_FAILURE=1

export FELIX_SE_HOME

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
  # Create symlink to log within Stitching Entity Resource Manager if not previously there
  if [ ! -L /var/log/$FELIX_SE_NAME ]; then
   ln -sf $LOG_FOLDER/ /var/log/$FELIX_SE_NAME
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
  ro_p_id=`ps ax | grep "stitching-entity" | grep "main.py" | grep -v "grep" | awk '{print $1}'`
  [ "$ro_p_id" != "" ] && kill -s KILL $ro_p_id || :
  return "$RETVAL"
}

do_restart() {
  do_stop
  sleep 1
  do_start
}

do_check_status() {
  if [ "$PID" != "" ]; then
   STATUS="running (pid $PID)"
  else
   STATUS="NOT running"
  fi
  echo "$FELIX_SE_TITLE is $STATUS."
}

case "$1" in
  start)
    action="Starting $FELIX_SE_TITLE.";
    echo $action;
    do_start;
    exit $?
  ;;
  stop)
    action="Stopping $FELIX_SE_TITLE.";
    echo $action;
    do_stop;
    exit $?
  ;;
  force-reload|restart)
    action="Restarting $FELIX_SE_TITLE.";
    echo $action;
    do_restart;
    exit $?
  ;;
  status)
    do_check_status;
    exit $?
  ;;
  *)
    echo "Usage: service $FELIX_SE_NAME {start|stop|restart|force-reload|status}";
    exit $RET_SUCCESS
  ;;
esac
