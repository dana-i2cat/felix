#!/bin/bash

# Set your GCF path here
gcf_path="/opt/geni/gcf-2.4"

echo ".............................."
echo "GENI v3. GetVersion"
echo ".............................."
python $gcf_path/src/omni.py -o -a https://localhost:8440/geni/3 -V 3 --debug getversion

echo ".............................."
echo "GENI v3. ListResources"
echo ".............................."
python $gcf_path/src/omni.py -o -a https://localhost:8440/geni/3 -V 3 --debug --no-compress listresources
