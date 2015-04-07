#! /bin/bash

# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
