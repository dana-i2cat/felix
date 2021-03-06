#!/bin/bash

# Set your GCF path here
gcf_path="/opt/geni/gcf-2.5"

## Two first commands should be run manually

echo ".............................."
echo "GENI. Starting Clearinghouse"
echo ".............................."
python $gcf_path/src/gcf-ch.py &

sleep .5

echo ".............................."
echo "RO. Starting main server"
echo ".............................."
python ../main.py &

sleep .5

echo ".............................."
echo "GENI v3. GetVersion"
echo ".............................."
python $gcf_path/src/omni.py -o -a https://localhost:8440/geni/3 -V 3 --debug getversion

echo ".............................."
echo "GENI v3. ListResources"
echo ".............................."
python $gcf_path/src/omni.py -o -a https://localhost:8440/geni/3 -V 3 --debug --no-compress listresources

echo ".............................."
echo "Killing server processes"
echo ".............................."
#ps axf | grep "main.py" | grep "python" | grep -v grep | awk '{print "kill -9 " $1}'
kill $(ps aux | grep "main.py" | grep "python" | grep -v grep | awk '{print $2}')
#ps axf | grep "gcf-ch.py" | grep "python" | grep -v grep | awk '{print "kill -9 " $1}'
kill $(ps aux | grep "gcf-ch.py" | grep "python" | grep -v grep | awk '{print $2}')
