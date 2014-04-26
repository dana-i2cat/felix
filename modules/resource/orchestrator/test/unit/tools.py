import sys
import os.path
import pprint
import xmlrpclib

def api_call(method_name, endpoint, params=[], user_name='alice', verbose=False):
    key_path, cert_path = "%s-key.pem" % (user_name,), "%s-cert.pem" % (user_name,)
    res = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path)
    if verbose:
        print_call(method_name, params, res)
    return res.get('code', None), res.get('value', None), res.get('output', None)

class SafeTransportWithCert(xmlrpclib.SafeTransport):
    """Helper class to force the right certificate for the transport class."""
    def __init__(self, key_path, cert_path):
        xmlrpclib.SafeTransport.__init__(self) # no super, because old style class
        self._key_path = key_path
        self._cert_path = cert_path

    def make_connection(self, host):
        """This method will automatically be called by the ServerProxy class when a transport channel is needed."""
        host_with_cert = (host, {'key_file' : self._key_path, 'cert_file' : self._cert_path})
        return xmlrpclib.SafeTransport.make_connection(self, host_with_cert) # no super, because old style class

def ssl_call(method_name, params, endpoint, key_path='alice-key.pem', cert_path='alice-cert.pem', host='127.0.0.1', port=8440):
    creds_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../..', 'cert'))
    if not os.path.isabs(key_path):
        key_path = os.path.join(creds_path, key_path)
    if not os.path.isabs(cert_path):
        cert_path = os.path.join(creds_path, cert_path)
    key_path = os.path.abspath(os.path.expanduser(key_path))
    cert_path = os.path.abspath(os.path.expanduser(cert_path))
    if not os.path.isfile(key_path) or not os.path.isfile(cert_path):
        raise RuntimeError("Key or cert file not found (%s, %s)" % (key_path, cert_path))
    transport = SafeTransportWithCert(key_path, cert_path)
    proxy = xmlrpclib.ServerProxy("https://%s:%s/%s" % (host, str(port), endpoint), transport=transport)
    # return proxy.get_version()
    method = getattr(proxy, method_name)

    return method(*params)

def get_creds_file_contents(filename):
    creds_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../..', 'creds'))
    if not os.path.isabs(filename):
        filename = os.path.join(creds_path, filename)
    filename = os.path.abspath(os.path.expanduser(filename))
    contents = None
    with open(filename, 'r') as f:
        contents = f.read()
    return contents

COLORS={"reset":"\x1b[00m",
    "blue":   "\x1b[01;34m",
    "cyan":   "\x1b[01;36m",
    "green":  "\x1b[01;32m",
    "yellow": "\x1b[01;33m",
    "red":    "\x1b[01;05;37;41m"}

def print_call(method_name, params, res):
    # output stuff
    print COLORS["blue"],
    print "--> %s(%s)" % (method_name, params)
    print COLORS["cyan"],
    pprint.pprint(res, indent=4, width=20)
    print COLORS["reset"]

WARNINGS = []

def warn(msg):
    global WARNINGS
    WARNINGS.append(msg)

def print_warnings():
    global WARNINGS
    if len(WARNINGS) > 0:
        print COLORS["yellow"],
        print
        print "WARNINGS:"
        for msg in WARNINGS:
            print msg
        print COLORS["reset"]
