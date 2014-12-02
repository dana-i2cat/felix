import tempfile
import uuid
import os
import os.path

from ext.geni.util.urn_util import URN
from ext.sfa.trust.gid import GID
# import ext.geni
from ext.sfa.trust.certificate import Keypair
from ext.geni.util import cert_util as gcf_cert_util
from ext.geni.util import cred_util as gcf_cred_util
import ext.sfa.trust.credential as sfa_cred
import ext.sfa.trust.rights as sfa_rights
from ext.sfa.util.faults import SfaFault
import ext.geni

from amsoil.core import serviceinterface

@serviceinterface
def decode_urn(urn):
    """Returns authority, type and name associated with the URN as string.
    example call:
      authority, typ, name = decode_urn("urn:publicid:IDN+eict.de+user+motine")
    """
    urn = URN(urn=str(urn))
    return urn.getAuthority(), urn.getType(), urn.getName()

@serviceinterface
def encode_urn(authority, typ, name):
    """
    Returns a URN string with the given {authority}, {typ}e and {name}.
    {typ} shall be either of the following: authority, slice, user, sliver, (project or meybe others: http://groups.geni.net/geni/wiki/GeniApiIdentifiers#Type)
    example call:
      urn_str = encode_urn("eict.de", "user", "motine")
    """
    return URN(authority=authority, type=typ, name=name).urn_string()

@serviceinterface
def create_certificate(urn, issuer_key=None, issuer_cert=None, is_ca=False,
                       public_key=None, life_days=1825, email=None, uuidarg=None):
    """Creates a certificate.
    {issuer_key} private key of the issuer. can either be a string in pem format or None.
    {issuer_cert} can either be a string in pem format or None.
    If either {issuer_cert} or {issuer_key} is None, the cert becomes self-signed
    {public_key} contains the pub key which will be embedded in the certificate. If None a new key is created, otherwise it must be a string)
    {uuidarg} can be a uuid.UUID or a string.

    Returns tuple in the following order:
      x509 certificate in PEM format
      public key of the keypair related to the new certificate in PEM format
      public key of the keypair related to the new certificate in PEM format or None if the the {public_key} was given.

    IMPORTANT
    Do not add an email when creating sa/ma/cm. This may lead to unverificable certs later.
    """
    # create temporary files for some params, because gcf's create_cert works with files and I did not want to duplicate the code
    pub_key_param = None
    if public_key:
        fh, pub_key_param = tempfile.mkstemp(); os.write(fh, public_key); os.close(fh)
    issuer_key_param, issuer_cert_param = None, None
    if issuer_key and issuer_cert:
        fh, issuer_key_param = tempfile.mkstemp(); os.write(fh, issuer_key); os.close(fh)
        fh, issuer_cert_param = tempfile.mkstemp(); os.write(fh, issuer_cert); os.close(fh)

    cert_gid, cert_keys = gcf_cert_util.create_cert(urn, issuer_key_param, issuer_cert_param, is_ca, pub_key_param, life_days, email, uuidarg)
    if pub_key_param:
        os.remove(pub_key_param)
    if issuer_key_param:
        os.remove(issuer_key_param)
    if issuer_cert_param:
        os.remove(issuer_cert_param)

    priv_key_result = None
    if not public_key:
        priv_key_result = cert_keys.as_pem()
    return cert_gid.save_to_string(), cert_keys.get_m2_pkey().get_rsa().as_pem(), priv_key_result

@serviceinterface
def create_slice_certificate(slice_urn, issuer_key, issuer_cert, expiration):
    """Returns only the x509 certificate as string (as PEM)."""
    return create_certificate(slice_urn, issuer_key, issuer_cert, uuidarg=uuid.uuid4())[0]

@serviceinterface
def create_credential(owner_cert, target_cert, issuer_key, issuer_cert, typ, expiration, delegatable=False):
    """
    {expiration} can be a datetime.datetime or a int/float (see http://docs.python.org/2/library/datetime.html#datetime.date.fromtimestamp) or a string with a UTC timestamp in it
    {typ} is used to determine the rights (via ext/sfa/truse/rights.py) can either of the following: "user", "sa", "ma", "cm", "sm", "authority", "slice", "component" also you may specify "admin" for all privileges.
    Returns the credential as String
    """
    ucred = sfa_cred.Credential()
    ucred.set_gid_caller(GID(string=owner_cert))
    ucred.set_gid_object(GID(string=target_cert))
    ucred.set_expiration(expiration)

    if typ == "admin":
        if delegatable:
            raise ValueError("Admin credentials can not be delegatable")
        privileges = sfa_rights.Rights("*")
    else:
        privileges = sfa_rights.determine_rights(typ, None)
        privileges.delegate_all_privileges(delegatable)
    ucred.set_privileges(privileges)
    ucred.encode()

    issuer_key_file, issuer_key_filename = tempfile.mkstemp(); os.write(issuer_key_file, issuer_key); os.close(issuer_key_file)
    issuer_cert_file, issuer_cert_filename = tempfile.mkstemp(); os.write(issuer_cert_file, issuer_cert); os.close(issuer_cert_file)

    ucred.set_issuer_keys(issuer_key_filename, issuer_cert_filename) # priv, gid
    ucred.sign()

    os.remove(issuer_key_filename)
    os.remove(issuer_cert_filename)

    return ucred.save_to_string()

@serviceinterface
def extract_certificate_info(certificate):
    """Returns the urn, uuid and email of the given certificate."""
    user_gid = GID(string=certificate)
    user_urn = user_gid.get_urn()
    user_uuid = user_gid.get_uuid()
    user_email = user_gid.get_email()
    return user_urn, user_uuid, user_email

@serviceinterface
def verify_certificate(certificate, trusted_cert_path=None):
    """
    Taken from ext...gid
    Verifies the chain of authenticity of the GID. First performs the checks of the certificate class (verifying that each parent signs the child, etc).
    In addition, GIDs also confirm that the parent's HRN is a prefix of the child's HRN, and the parent is of type 'authority'.

    Raises a ValueError if bad certificate.
    Does not return anything if successful.
    """
    try:
        trusted_certs = None
        if trusted_cert_path:
            trusted_certs_paths = [os.path.join(os.path.expanduser(trusted_cert_path), name) for name in os.listdir(os.path.expanduser(trusted_cert_path)) if (name != gcf_cred_util.CredentialVerifier.CATEDCERTSFNAME) and (name[0] != '.')]
            trusted_certs = [GID(filename=name) for name in trusted_certs_paths]
        gid = GID(string=certificate)
        gid.verify_chain(trusted_certs)
    except SfaFault as e:
        raise ValueError("Error verifying certificate: %s" % (str(e),))
    return None

@serviceinterface
def verify_credential(credentials, owner_cert, target_urn, trusted_cert_path, privileges=()):
    """
    Give a list of credentials and they will be checked to have the privleges and to be trusted by the trusted_certs.
    The privileges should be tuple.

    To verify a user: owner_cert=user_cert, target_urn=user
    To verify a slice: owner_cert=user_cert, target_urn=slice_urn

    {credentials} a list of strings (["CRED1", "CRED2"]) or a list of dictionaries [{"SFA" : "CRED1"}, {"ABAC" : "CRED2"}]
    {owner_cert} a string with the cert in PEM format
    {target_urn} a string with a urn
    {trusted_cert_path} a string containing the file system path with files (trusted certificates) in pem format in it
    {privileges} a list of the privileges (see below)

    Here a list of possible privileges (format: right_in_credential: [privilege1, privilege2, ...]):
        "authority" : ["register", "remove", "update", "resolve", "list", "getcredential", "*"],
        "refresh"   : ["remove", "update"],
        "resolve"   : ["resolve", "list", "getcredential"],
        "sa"        : ["getticket", "redeemslice", "redeemticket", "createslice", "createsliver", "deleteslice", "deletesliver", "updateslice",
                       "getsliceresources", "getticket", "loanresources", "stopslice", "startslice", "renewsliver",
                        "deleteslice", "deletesliver", "resetslice", "listslices", "listnodes", "getpolicy", "sliverstatus"],
        "embed"     : ["getticket", "redeemslice", "redeemticket", "createslice", "createsliver", "renewsliver", "deleteslice",
                       "deletesliver", "updateslice", "sliverstatus", "getsliceresources", "shutdown"],
        "bind"      : ["getticket", "loanresources", "redeemticket"],
        "control"   : ["updateslice", "createslice", "createsliver", "renewsliver", "sliverstatus", "stopslice", "startslice",
                       "deleteslice", "deletesliver", "resetslice", "getsliceresources", "getgids"],
        "info"      : ["listslices", "listnodes", "getpolicy"],
        "ma"        : ["setbootstate", "getbootstate", "reboot", "getgids", "gettrustedcerts"],
        "operator"  : ["gettrustedcerts", "getgids"],
        "*"         : ["createsliver", "deletesliver", "sliverstatus", "renewsliver", "shutdown"]

    When using the gcf clearinghouse implementation the credentials will have the rights:
    - user: "refresh", "resolve", "info" (which resolves to the privileges: "remove", "update", "resolve", "list", "getcredential", "listslices", "listnodes", "getpolicy").
    - slice: "refresh", "embed", "bind", "control", "info" (well, do the resolving yourself...)
    """

    creds = credentials # strip the type info if a list of dicts is given
    if len(credentials) > 0 and isinstance(credentials[0], dict):
        creds = [cred.values()[0] for cred in credentials]
    try:
        cred_verifier = ext.geni.CredentialVerifier(trusted_cert_path)
        cred_verifier.verify_from_strings(owner_cert, creds, target_urn, privileges)
    except Exception as e:
        raise ValueError("Error verifying the credential: %s" % (str(e),))
