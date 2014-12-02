#! /bin/bash
#
#LIBS=jpywork
#LIBS=./
LIBS=jpywork:./
NSI_HOME=/home/okazaki/nsi2/java
LIBS=./
#LIBS=$LIBS:${NSI_HOME}/common/build/jar/common.jar
LIBS=$LIBS:${NSI_HOME}/clientapi/build/jar/nsi2_client.jar
LIBS=$LIBS:${NSI_HOME}/nrm/build/jar/aist_upa.jar
LIBS=$LIBS:${NSI_HOME}/nrm/lib/commons-logging-1.1.1.jar
LIBS=$LIBS:${NSI_HOME}/nrm/lib/log4j-1.2.13.jar
for i in ${CXF_HOME}/lib/*.jar
do
   LIBS=$LIBS:"$i"
done
export CLASSPATH=$LIBS

LOGFILE=/tmp/test.log

#jython main.jy
#jython  main.jy
env CLASSPATH=$LIBS jython -v proxy.py 2>&1 | tee $LOGFILE 
#env CLASSPATH=$LIBS jython -v nsi2interface.py 2>&1 | tee $LOGFILE 
