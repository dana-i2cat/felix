__author__ = 'umar.toseef'

import ABAC
import sys
import os
import glob
import OpenSSL.crypto

dir_path = 'deploy/trusted/certs/'
cbas_cert_path = 'deploy/trusted/certs/ca-cert.pem'
cbas_key_path = 'deploy/trusted/cert_keys/ca-key.pem'


def create_credentials(output_file_name, issuer_cert, issuer_key, target_cert, role=None):

    ctx = ABAC.Context()

    try:
        issuer_id = ABAC.ID(issuer_cert)
        issuer_id.load_privkey(issuer_key)
        mnemonic1 = get_common_name(issuer_cert)
        if mnemonic1:
            ctx.load_id_file(issuer_cert)
            ctx.set_nickname(issuer_id.keyid(), str(mnemonic1))
    except ValueError:
        print "Could not load issuer certificate/key file"
        sys.exit(1)

    try:
        target_id = ABAC.ID(target_cert)
        if not role:
            mnemonic2 = get_common_name(target_cert)
            if mnemonic2:
                ctx.load_id_file(target_cert)
                ctx.set_nickname(target_id.keyid(), str(mnemonic2))
    except ValueError:
        print "Could not load target certificate file: "+target_cert
        sys.exit(1)

    if not role:
        attr = ABAC.Attribute(issuer_id, "Trusted", 24 * 3600 * 365 * 10)
        attr.principal(target_id.keyid())
    elif role == 'speaks_for':
        attr = ABAC.Attribute(issuer_id, "speaks_for_"+str(issuer_id.keyid()), 24 * 3600 * 365 * 10)
        attr.role(target_id.keyid(), "Trusted")
    elif role == 'Trusted':
        attr = ABAC.Attribute(issuer_id, "Trusted", 24 * 3600 * 365 * 10)
        attr.role(target_id.keyid(), "Trusted")
    else:
        print 'Unrecognized role. Aborting...'

    attr.bake(ctx)

    attr.write_file(output_file_name+"-speaks_for.xml")
    print 'Writing credential file: '+output_file_name+"-speaks_for.xml"


def get_common_name(certfile):

    cn = None
    try:
        st_cert = open(certfile, 'rt').read()
        c = OpenSSL.crypto
        cert = c.load_certificate(c.FILETYPE_PEM, st_cert)
        cn = cert.get_subject().commonName
    except:
        pass
    return cn

if __name__ == "__main__":
    print ""
    print "1. Issue speaks_for credential to a user"
    print "2. Issue speaks_for credential to an RO"
    print "3. Acting as a non-master island, issue speaks_for credential to master island"
    print "4. Acting as a master island, issue speaks_for credential to other islands"
    print
    op = input("Select mode of operation (1-4): ")
    if op == 4:
        print "Creating speaks_for credentials for all trusted islands..."
        cert_list = glob.glob(dir_path+'*+ca-cert.pem')
        for cert_path in cert_list:
            output_file = cert_path[len(dir_path):cert_path.find('+')]
            create_credentials(output_file, cbas_cert_path, cbas_key_path, cert_path, 'Trusted')

    elif op == 3:
        input_str = raw_input("Enter master cbas name (e.g., mcbas.i2cat.net):").strip()
        mcbas_cert_path = dir_path+input_str+'+authority+ca-cert.pem'
        if not os.path.isfile(mcbas_cert_path):
            print 'certificate for provided name does not exist under '+dir_path
            print 'aborting...'
            sys.exit(1)
        else:
            create_credentials(input_str, cbas_cert_path, cbas_key_path, mcbas_cert_path, 'Trusted')

    elif op == 1:
        cert_file = raw_input("Enter user cert file: ").strip()
        if not os.path.isfile(cert_file):
            print 'given certificate file does not exist'
            print 'aborting...'
            sys.exit(1)
        key_file = cert_file.replace('-cert','-key')
        if not os.path.isfile(key_file) or key_file == cert_file:
            key_file = raw_input("Enter user cert key file: ")
            if not os.path.isfile(key_file):
                print 'given certificate key file does not exist'
                print 'aborting...'
                sys.exit(1)

        output_file = cert_file[cert_file.rfind('/')+1:cert_file.find('-cert')] if cert_file.find('-cert') >0 else 'output'
        create_credentials(output_file, cert_file, key_file, cbas_cert_path, 'speaks_for')

    elif op == 2:
        cert_file = raw_input("Enter RO cert file: ").strip()
        if not os.path.isfile(cert_file):
            print 'given certificate file does not exist'
            print 'aborting...'
            sys.exit(1)

        output_file = cert_file[cert_file.rfind('/')+1:cert_file.find('-cert')] if cert_file.find('-cert') >0 else 'output'
        create_credentials(output_file, cbas_cert_path, cbas_key_path, cert_file)
    else:
        print 'Entered invalid option. Aborting...'







# try:
#     user_id = ABAC.ID("/root/.gcf/bob-cert.pem")
#     user_id.load_privkey("/root/.gcf/bob-key.pem")
# except ValueError:
#     print "Could not read id from given user certificate file"
#     sys.exit(1)
#
# try:
#     cbas_id = ABAC.ID("/root/.gcf/bob-cert.pem")
# except ValueError:
#     print "Could not read id from given CH certificate file"
#     sys.exit(1)
#
# attr = ABAC.Attribute(user_id, "speaks_for_"+str(user_id.keyid()), 24 * 3600 * 365)
# attr.principal(cbas_id.keyid())
# attr.role(cbas_id.keyid(), "Trusted")
#
# attr.bake()
#
# attr.write_file("attr.xml")
# cxt = ABAC.Context()
# cxt.load_attribute_chunk(attr.cert_chunk())
# ok, proof = cxt.query(user_id.keyid()+".speaks_for_"+str(user_id.keyid()), cbas_id.keyid()+".Trusted")
# for i, c in enumerate(proof):
#     print "%s <- %s" % (c.head().string(), c.tail().string())
