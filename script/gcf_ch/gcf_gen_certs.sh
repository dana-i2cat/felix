#!/bin/bash

USER=`whoami`
if [ $USER == "root" ]; then
  HOME_DIR="/root"
else
  HOME_DIR="/home/$USER"
fi
OPENSSL_LOCAL_DIR="$HOME_DIR/.gcf.openssl"

# Create environment
mkdir -p $OPENSSL_LOCAL_DIR
cp -p ca.cnf ro.cnf $OPENSSL_LOCAL_DIR/
cd $OPENSSL_LOCAL_DIR

# Clean-up
rm -f *.pem
rm -f index.txt*
rm -f serial.txt
touch index.txt
echo "01" > serial.txt

# Create selfsigned certificate and key for CA
openssl req -x509 -config ca.cnf -newkey rsa:1024 -sha256 -nodes -out ca-cert.pem -outform PEM

# Create Alice's key and certificate signed by MA
openssl req -config ro.cnf -newkey rsa:1024 -sha256 -nodes -out ro-cert.csr -outform PEM
openssl ca -config ca.cnf -policy signing_policy -extensions signing_req -out ro-cert.pem -infiles ro-cert.csr

# Use CA cert as GCF Clearinghouse cert
cp ca-cert.pem ch-cert.pem
cp ca-key.pem ch-key.pem

# Use RO cert as Alice cert
cp ro-cert.pem alice-cert.pem
cp ro-key.pem alice-key.pem

# Backup current .gcf environment
BACKUP_DIR="$HOME_DIR/.gcf__"`date +%Y_%m_%d-%H_%M_%S`
if [ -d ~/.gcf ]; then
    cp -Rp ~/.gcf $BACKUP_DIR
else
  mkdir -p ~/.gcf
fi
mkdir -p ~/.gcf/trusted_roots

# Place files in appropriate folder
cp -p alice-cert.pem ~/.gcf/alice-cert.pem
cp -p alice-key.pem ~/.gcf/alice-key.pem
cp -p ch-cert.pem ~/.gcf/ch-cert.pem
cp -p ch-key.pem ~/.gcf/ch-key.pem
cp -p ch-cert.pem ~/.gcf/trusted_roots/ch-cert.pem
cat ch-cert.pem >> ~/.gcf/trusted_roots/CATedCACerts.pem
openssl x509 -in ch-cert.pem >> ~/.gcf/trusted_roots/CATedCACerts.pem

echo "------------"
echo "OpenSSL certificate to be placed in trusted_roots for each RM:"
echo ""
openssl x509 -in ch-cert.pem
echo "------------"
