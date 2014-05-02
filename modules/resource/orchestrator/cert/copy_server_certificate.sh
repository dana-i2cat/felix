#!/bin/bash

# Copy GCF trusted root certificate in RO's trusted root path
# (Ideally, only one...)
mkdir -p trusted
cp -p ~/.gcf/trusted_roots/CATedCACerts.pem trusted/server.pem
