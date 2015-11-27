Certificates folder
===================

1. Place the user required files under (M)RO's `cert` folder.
  * Run `./copy_alice_credentials.sh` in this folder.
  * _Note1_: this will attempt to copy the user cert under the name of 'alice' from typically used folders:
    * GENI CH: `~/.gcf/alice-cert.pem`, `~/.gcf/alice-key.pem`
    * CBAS CH: (GENI CH) + `~/.gcf/alice-cred.xml`
  * _Note2_: if certs not present, generate them from your CH:
    * GENI CH: `gen-certs.py` from GCF source folder.
    * CBAS CH: `test/creds/gen-certs.sh` from CBAS source folder.

1. Place the CA certificate of your CH under the `cert/trusted` folder.
  * Run `./trust_ch_certificate.sh` in this folder.
  * _Note3_: this will attempt to copy CA certificate from typically used folders:
    * GENI CH: `~/.gcf/trusted_roots/CATedCACerts.pem`
    * CBAS CH: `/opt/felix/cbas/deploy/trusted/certs/ca-cert.pem`

1. Generate the certificate for your (M)RO's server.
  * Run `./generate_server_cert_key.sh` in this folder.
