import sys
import os.path
import pprint
import xmlrpclib

#from dossl import *
import credparsing as credutils

def api_call(method_name, endpoint, params=[], user_name='alice', verbose=False):
    key_path, cert_path = "%s-key.pem" % (user_name,), "%s-cert.pem" % (user_name,)
    res = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path)
    if verbose:
        print_call(method_name, params, res)
    return res.get('code', None), res.get('value', None), res.get('output', None)

def ch_call(method_name, endpoint="", params=[], user_name='alice', verbose=False):
    key_path, cert_path = "%s-key.pem" % (user_name,), "%s-cert.pem" % (user_name,)
    res = ssl_call(method_name, {}, "/", key_path=key_path, cert_path=cert_path, host='127.0.0.1', port=8000)
    print "\n\n\n\nRES........... :%s\n\n\n" % str(res)
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
    print "........... before error"
    # return proxy.get_version()
    method = getattr(proxy, method_name)
    #print ".......... method: %s" % str(method)
    return method(*params)

#def load_framework(config, opts):
#    """Select the Control Framework to use from the config, and instantiate the proper class."""
#
#    cf_type = config['selected_framework']['type']
#    config['logger'].debug('Using framework type %s', cf_type)
#
#    framework_mod = __import__('omnilib.frameworks.framework_%s' % cf_type, fromlist=['omnilib.frameworks'])
#    config['selected_framework']['logger'] = config['logger']
#    framework = framework_mod.Framework(config['selected_framework'], opts)
#    return framework

#def wrap_cred(self, cred):
#    """
#    Wrap the given cred in the appropriate struct for this framework.
#    """
#    if isinstance(cred, dict):
#        print "Called wrap on a cred that's already a dict? %s", cred
#        return cred
#    elif not isinstance(cred, str):
#        print "Called wrap on non string cred? Stringify. %s", cred
#        cred = str(cred)
#    ret = dict(geni_type="geni_sfa", geni_version="2", geni_value=cred)
#    if credutils.is_valid_v3(self.logger, cred):
#        ret["geni_version"] = "3"
#    return ret

def getusercred(user_cert_filename = "alice-cert.pem", geni_api = 3):
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
    creds_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../..', 'cert'))
    cert_path = os.path.join(creds_path, user_cert_filename)
    user_cert = open(cert_path, "r").read()

#    ch = make_client(config['ch'], self.key, self.cert,
#                           verbose=config['verbose'])
#            return omnilib.xmlrpc.client.make_client(url, keyfile, certfile,
#                                                 verbose=verbose,
#                                                 timeout=timeout,
#                                                 allow_none=allow_none)

# res = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path)

    if geni_api >= 3:
        #(cred, message) = self.framework.get_user_cred_struct()
#        (cred, message) = ssl_call(method_name, params, endpoint, key_path=key_path, cert_path=cert_path)
#        (cred, message) = _do_ssl(self, None, ("Create user credential on GCF CH %s" % self.config['ch']), self.ch.CreateUserCredential, user_cert)
        (cred, message) = ch_call("CreateUserCredential")
        if cred:
            cred = wrap_cred(cred)
    else:
        #(cred, message) = self.framework.get_user_cred()
#        (cred, message) = _do_ssl(self, None, ("Create user credential on GCF CH %s" % self.config['ch']), self.ch.CreateUserCredential, user_cert)
        (cred, message) = ch_call("CreateUserCredential")
    credxml = credutils.get_cred_xml(cred)
    if cred is None or credxml is None or credxml == "":
        msg = "Got no valid user credential from framework: %s" % message
#        if self.opts.devmode:
#            self.logger.warn(msg + " ... but continuing")
#            credxml = cred
#        else:
#            self._raise_omni_error(msg)
#    target = credutils.get_cred_target_urn(None, cred)
    # pull the username out of the cred
    # <owner_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</owner_urn>
    user = ""
    usermatch = re.search(r"\<owner_urn>urn:publicid:IDN\+.+\+user\+(\w+)\<\/owner_urn\>", credxml)
    if usermatch:
        user = usermatch.group(1)
#    if self.opts.output:
#        if self.opts.usercredfile and self.opts.usercredfile.strip() != "":
#            fname = self.opts.usercredfile
#        else:
#            fname = self.opts.framework + "-usercred"
#            if user != "":
#                fname = user + "-" + fname
#            if self.opts.prefix and self.opts.prefix.strip() != "":
#                fname = self.opts.prefix.strip() + "-" + fname
#        filename = self._save_cred(fname, cred)
#        self.logger.info("Wrote %s user credential to %s" % (user, filename))
#        self.logger.debug("User credential:\n%r", cred)
#        return "Saved user %s credential to %s" % (user, filename), cred
#    elif self.opts.tostdout:
    if user != "":
        print "Writing user %s usercred to STDOUT per options", user
    else:
        print "Writing usercred to STDOUT per options"
    # pprint does bad on XML, but OK on JSON
    print cred
    if user:
        return "Printed user %s credential to stdout" % user, cred
    else:
        return "Printed user credential to stdout", cred
    return "Retrieved %s user credential" % user, cred

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
