#!/bin/bash

if [ -f ~/.gcf/alice-cert.pem ]; then
  cp -p ~/.gcf/alice-cert.pem alice-cert.pem
fi
if [ -f ~/.gcf/alice-key.pem ]; then
  cp -p ~/.gcf/alice-key.pem alice-key.pem
fi
if [ -f ~/.gcf/alice-cred.xml ]; then
  cp -p ~/.gcf/alice-cred.xml alice-cred.xml
fi
