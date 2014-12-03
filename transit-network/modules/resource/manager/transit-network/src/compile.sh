#! /bin/bash
NSI_HOME=/home/okazaki/nsi2/java
LIBS=./
#LIBS=$LIBS:${NSI_HOME}/common/build/jar/common.jar
LIBS=$LIBS:${NSI_HOME}/clientapi/build/jar/nsi2_client.jar
#LIBS=$LIBS:${NSI_HOME}/nrm/build/jar/aist_upa.jar
LIBS=$LIBS:${NSI_HOME}/nrm/lib/commons-logging-1.1.1.jar
LIBS=$LIBS:${NSI_HOME}/nrm/lib/log4j-1.2.13.jar
for i in ${CXF_HOME}/lib/*.jar
do
   LIBS=$LIBS:"$i"
done

# echo javac -cp $LIBS NSI2Interface.java
javac -cp $LIBS NSI2Interface.java
