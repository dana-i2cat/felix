#!/bin/bash

# Copy trusted CA certificates for CH under RO's cert/trusted folder
mkdir -p trusted

ro_trusted_ca="trusted/ch.pem"
gcf_ca="~/.gcf/trusted_roots/CATedCACerts.pem"
cbas_ca="/opt/felix/cbas/deploy/trusted/certs/ca-cert.pem"

if [ -f $gcf_ca ]; then
  cp -p $gcf_ca $ro_trusted_ca
elif [ -f $cbas_ca ]; then
  cp -p $cbas_ca $ro_trusted_ca
fi
