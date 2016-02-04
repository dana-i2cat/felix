#! /bin/bash
#
ORGDIR=/home/okazaki/AMsoil/tnrm/src/vendor/tnrm

for f in *.py ; do
    echo $f
    diff $f $ORGDIR/$f
    echo "=========================================================="
done

for f in  compile.sh config.xml MANIFEST.json NSI2Interface.java proxy.sh README.me; do
    echo $f
    diff $f $ORGDIR/$f
    echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
done