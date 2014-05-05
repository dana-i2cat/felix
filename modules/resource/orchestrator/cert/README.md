Certificates folder
===================

1. Place your GENI Control Framework's certificate and key for user 'alice' within this folder.
  * Run `./copy_alice_credentials.sh` in this folder.
  * When not present, please run `gen-certs.py` from your GCF source folder.

1. Place your CH certificate within the `trusted` folder.
  * Run `./copy_server_certificate.sh` in this folder (valid for GENI clearinghouse).

1. Place the CH certificate in the appropriate place of each Resource Manager.
  * Copy the certificate under `trusted` into their `trusted_roots` folder.
