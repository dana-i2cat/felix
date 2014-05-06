#!/bin/sh

## Daemonizer for the FELIX Resource Orchestrator.
## Expected to work under both Debian-based systems and RedHat.
## Version: 0.1
## Author: Carolina Fernandez
## Organization: i2CAT

# chkconfig: 2345 80 20
# description: startup script for FELIX Resource Orchestrator

### BEGIN INIT INFO
# Provides: felix-ro
# Required-Start: $local_fs $remote_fs $network $syslog
# Required-Stop: $local_fs $remote_fs $network $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: startup script for FELIX Resource Orchestrator
### END INIT INFO
#


# Name for the service, used in logging
FELIX_RO_NAME=felix-ro

# Title for the service, used in service commands
FELIX_RO_TITLE="FELIX Resource Orchestrator"

# Name of the user to be used to execute the service
#FELIX_RO_USER=root
FELIX_RO_USER=i2cat

# In which directory is the shell script that this service will execute
#FELIX_RO_HOME=/opt/felix/felix-dev/modules/resource/orchestrator
FELIX_RO_HOME=/opt/felix/resource-orchestrator/modules/resource/orchestrator

# Where to write the process identifier - this is used to track if the service is already running 
# Note: the script noted in the COMMAND must actually write this file 
PID_FILE=/var/run/$FELIX_RO_NAME.pid

# File to handle instances of the program
LOCK_FILE=/var/lock/$FELIX_RO_NAME

# Where to write the spreader log file
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

do_start() {
	if [ "$PID" != "" ]; then
		# Check to see if the /proc dir for this process exists
		if [ -f "/proc/$PID" ]]; then
			# Check to make sure this is likely the running service
			ps aux | grep $PID | grep $PROCESS_TYPE >> /dev/null
			# If process of the right type, then is daemon and exit 
			if [ "$?" = "0" ]; then
				return $RET_SUCCESS
			else
				# Otherwise remove the subsys lock file and start daemon 
				echo "$FELIX_RO_TITLE is already running." 
				rm -f $LOCK_FILE
			fi
		else
			# The process running as pid $PID is not a process
			# of the right type; remove lock file
			rm -f $LOCK_FILE
		fi
	fi

	create_log

	# RedHat-based distros do not help too much with pidfiles creation, so it
	# is done manually by retrieving and killing the last created process (tail).
	if [ -e /etc/redhat-release ]; then
#		daemon $EXEC --pidfile $PID_FILE --user $FELIX_RO_USER start > \
#		/dev/null 2> /dev/null &
#		PID=`ps xaww | grep "$PROCESS_TYPE" | grep "$EXEC" | grep "pidfile $PID_FILE" | tail -1 | awk '{print $1}'`

		# Daemon opens N processes for Resource Orchestrator (shell, bash, python).
		# Using something more adequate, then retrieving its PID
		$EXEC > /dev/null 2> /dev/null &
		PID=`ps xaww | grep "$PROCESS_TYPE" | grep "$EXEC" | grep -v "grep" | tail -1 | awk '{print $1}'`
		echo $PID > $PID_FILE
	else
		start-stop-daemon --start --chuid $FELIX_RO_USER --user $FELIX_RO_USER \
		--name $FELIX_RO_USER -b --make-pidfile --pidfile $PID_FILE --exec $EXEC
	fi

	touch $LOCK_FILE
	echo
	return $RET_SUCCESS
}

do_stop() {
#	daemon $EXEC --pidfile $PID_FILE --user $FELIX_RO_USER stop > /dev/null 2> /dev/null &

	# Always remove control files on stop
	rm -f $LOCK_FILE
	rm -f $PID_FILE
	if [ "$PID" != "" ]; then
        PIDS=`ps xaww | grep "$PROCESS_TYPE" | grep "$EXEC" | grep -v "grep" | cut -d " " -f2`
        # XXX: Several processes are being initialised! Take care of them.
        for PID in "${PIDS##*:}"; do
            kill -QUIT $PID
        done
#		kill $PID
		for i in {1..30}
		do
			if [ -n "`ps aux | grep $PROCESS_TYPE | grep $FELIX_RO_NAME `" ]; then
				sleep 1 # Still running, wait a second
				echo -n . 
			else
				# Already stopped 
				echo 
				return $RET_SUCCESS
			fi
		done
	else
		echo "$FELIX_RO_TITLE is already NOT running."
		return $RET_SUCCESS
	fi
	# Should never reach this...?
	kill -QUIT $PID | return $RET_FAILURE # Instant death. If THAT fails, return error
	return $RET_SUCCESS
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
	restart|force-reload)
		action="Restarting $FELIX_RO_TITLE.";
		echo $action;
		do_restart;
		exit $?
	;;
	status)
		do_check_status;
		exit $?
	;;
	*)
		echo "Usage: service $FELIX_RO_NAME {start|stop|restart|force-reload|config|status}";
		exit $RET_SUCCESS
	;;
esac
