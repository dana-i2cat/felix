from formatting import print_call

import credentials
import os.path
import re
import xmlrpclib


def _get_ch_params():
    # Initialise variables when required
    from core.config import FullConfParser
    fcp = FullConfParser()
    username = fcp.get("auth.conf").get("certificates").get("username")
    ch_host = fcp.get("auth.conf").get("clearinghouse").get("host")
    ch_port = fcp.get("auth.conf").get("clearinghouse").get("port")
    ch_end = fcp.get("auth.conf").get("clearinghouse").get("endpoint")
    return (username, ch_host, ch_port, ch_end)

def api_call(method_name, endpoint=None, params=[], username=None, verbose=False):
    user, _, _, ch_end = _get_ch_params()
    username = username or user
    endpoint = endpoint or ch_end
    key_path, cert_path = "%s-key.pem" % (username,), "%s-cert.pem" % (username,)
    res = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path)
    if verbose:
        print_call(method_name, params, res)
    return res.get("code", None), res.get("value", None), res.get("output", None)

def ch_call(method_name, endpoint=None, params=[], username=None, verbose=False):
    user, ch_host, ch_port, ch_end = _get_ch_params()
    username = username or user
    endpoint = endpoint or ch_end
    key_path, cert_path = "%s-key.pem" % (username,), "%s-cert.pem" % (username,)
    res = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path, host=ch_host, port=ch_port)
    return res

def handler_call(method_name, params=[], username=None, arg=[]):
    if username is None:
        user, _, _, _ = _get_ch_params()
    verbose = False
    if arg in ["-v", "--verbose"]:
        verbose = True
    return api_call(method_name, "/xmlrpc/geni/3/", params=params, username=username, verbose=verbose)

class SafeTransportWithCert(xmlrpclib.SafeTransport):
    """Helper class to force the right certificate for the transport class."""
    def __init__(self, key_path, cert_path):
        xmlrpclib.SafeTransport.__init__(self) # no super, because old style class
        self._key_path = key_path
        self._cert_path = cert_path

    def make_connection(self, host):
        """This method will automatically be called by the ServerProxy class when a transport channel is needed."""
        host_with_cert = (host, {"key_file" : self._key_path, "cert_file" : self._cert_path})
        return xmlrpclib.SafeTransport.make_connection(self, host_with_cert) # no super, because old style class

def ssl_call(method_name, params, endpoint, key_path=None, cert_path=None, host=None, port=None):
    username, ch_host, ch_port, ch_end = _get_ch_params()
    key_path = key_path or ("%-key.pem" % username)
    cert_path = cert_path or ("%-cert.pem" % username)
    host = host or ch_host
    port = port or ch_port
    endpoint = endpoint or ch_end
    # Start logic
    creds_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../..", "cert"))
    if not os.path.isabs(key_path):
        key_path = os.path.join(creds_path, key_path)
    if not os.path.isabs(cert_path):
        cert_path = os.path.join(creds_path, cert_path)
    key_path = os.path.abspath(os.path.expanduser(key_path))
    cert_path = os.path.abspath(os.path.expanduser(cert_path))
    if not os.path.isfile(key_path) or not os.path.isfile(cert_path):
        raise RuntimeError("Key or cert file not found (%s, %s)" % (key_path, cert_path))
    transport = SafeTransportWithCert(key_path, cert_path)
    if endpoint and len(endpoint):
        if endpoint[0] == "/":
            endpoint = endpoint[1:]
    proxy = xmlrpclib.ServerProxy("https://%s:%s/%s" % (host, str(port), endpoint), transport=transport)
    # return proxy.get_version()
    method = getattr(proxy, method_name)
    return method(*params)

def getusercred(geni_api = 3):
    """Retrieve your user credential. Useful for debugging.

    If you specify the -o option, the credential is saved to a file.
    If you specify --usercredfile:
       First, it tries to read the user cred from that file.
       Second, it saves the user cred to a file by that name (but with the appropriate extension)
    Otherwise, the filename is <username>-<framework nickname from config file>-usercred.[xml or json, depending on AM API version].
    If you specify the --prefix option then that string starts the filename.

    If instead of the -o option, you supply the --tostdout option, then the usercred is printed to STDOUT.
    Otherwise the usercred is logged.

    The usercred is returned for use by calling scripts.

    e.g.:
      Get user credential, save to a file:
        omni.py -o getusercred

      Get user credential, save to a file with filename prefix mystuff:
        omni.py -o -p mystuff getusercred
    """
    from core.config import FullConfParser
    fcp = FullConfParser()
    username = fcp.get("auth.conf").get("certificates").get("username")
    creds_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../..", "cert"))
    cert_path = os.path.join(creds_path, "%s-cert.pem" % username)
    # Retrieve new credential by contacting with GCF CH
    try:
        user_cert = open(cert_path, "r").read()
        cred = ch_call("CreateUserCredential", params = [user_cert])
    # Exception? -> Retrieve already existing credential from disk (CBAS)
    except:
        cred_path = os.path.join(creds_path, "%s-cred.xml" % username)
        cred = open(cred_path).read()
    if geni_api >= 3:
        if cred:
            cred = credentials.wrap_cred(cred)
    credxml = credentials.get_cred_xml(cred)
    # pull the username out of the cred
    # <owner_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</owner_urn>
    user = ""
    usermatch = re.search(r"\<owner_urn>urn:publicid:IDN\+.+\+user\+(\w+)\<\/owner_urn\>", credxml)
    if usermatch:
        user = usermatch.group(1)
    return ("Retrieved %s user credential" % user, cred)

