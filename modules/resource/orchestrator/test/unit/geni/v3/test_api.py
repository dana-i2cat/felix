#!/usr/bin/env python


import datetime
import os
import sys
#import unittest
import unittest2 as unittest

# Adding paths to locate modules from other packages
sys.path.insert(0, "../../../../src")
from handler.geni.v3.extensions.geni.util import cred_util
from handler.geni.v3.extensions.sfa.trust import gid
sys.path.insert(1, "../..")
import tools

arg = None
# Get the cert_root from the configuration settings
cert_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../cert"))

def handler_call(method_name, params=[], user_name="alice"):
    if arg in ["-v", "--verbose"]:
        verbose = True
    else:
        verbose = False
    return tools.api_call(method_name, "geni/3", params=params, user_name=user_name, verbose=verbose)

class TestGENIv3API(unittest.TestCase):

    @classmethod
    def setUp(self):
        pass

    def test_get_version(self):
        """
        Test 'get_version' method.

        Check result for various valid/required fields.
        """
        code, value, output = handler_call("GetVersion")
        #print "... code: %s" % str(code)
        #print "... value: %s" % str(value)
        self.assertEqual(code.get("geni_code", None), 0) # no error
        self.assertIsInstance(value, dict)
        # Ensure keys from returned dictionary
        self.assertIn("geni_credential_types", value)
        self.assertIn("geni_request_rspec_versions", value)
        self.assertIn("geni_api_versions", value)
        self.assertIn("geni_api", value)
        self.assertIn("geni_ad_rspec_versions", value)
        self.assertIn("geni_single_allocation", value)
        self.assertIn("geni_allocate", value)
        # Check type of data in values from returned dictionary
        self.assertIsInstance(value["geni_credential_types"], dict)
        self.assertIsInstance(value["geni_request_rspec_versions"], list)
        self.assertIsInstance(value["geni_api_versions"], dict)
        self.assertIsInstance(value["geni_api"], str)
        self.assertIsInstance(value["geni_ad_rspec_versions"], list)
        self.assertIsInstance(value["geni_single_allocation"], bool)
        self.assertIsInstance(value["geni_allocate"], str)
        # Check data in values from returned dictionary
        self.assertEquals(value["geni_credential_types"]["geni_version"], "3")
        # ...
        self.assertEquals(value["geni_api_versions"].keys()[0], "3")
        self.assertEquals(value["geni_api_versions"].values()[0], "/geni/3")
        self.assertEquals(value["geni_api"], "3")

    def test_list_resources(self):
        #user_certfile = os.path.join(cert_root, "alice-cert.pem")
        # FIXME: Certificate is not a GID. This will not work
        #caller_gid = gid.GID(filename=user_certfile)
        #object_gid = caller_gid
        #caller_hrn = "geni.gpo.gcf.alice"
        #expiration = datetime.datetime.utcnow() + datetime.timedelta(days=100)
        #typename = "user"
        #issuer_keyfile = os.path.join(cert_root, "server.key")
        #issuer_certfile = os.path.join(cert_root, "server.crt")
        #trusted_roots = os.path.join(cert_root, "trusted", "server.pem")
        #user_credential = cred_util.create_credential(caller_gid, object_gid, expiration, typename, issuer_keyfile, issuer_certfile, trusted_roots, delegatable=False)
        user_credential = open(os.path.join(cert_root, "credentials", "alice-cred.xml"), "r").readlines()
        user_credential = "".join(user_credential)
        
        geni_v3_credentials = [{
            "geni_type": "geni_sfa",
            "geni_value": user_credential,
        }]
        # Any AM is required to honor the following options
        geni_v3_options = {
            "geni_available": True,
            # XXX: should be 'compressed' (as in GENIv3), not 'compress' (as in AMsoil)
            # http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#ListResources
            #"geni_compressed": True,
            "geni_compress": True,
            "geni_rspec_version": {
                "type": "geni",
                "version": "3",
            }
        }
        params = [
            geni_v3_credentials,
            geni_v3_options,
        ]
        code, value, output = handler_call("ListResources", params=params)
        #print "... code: %s" % str(code)
        #print "... value: %s" % str(value)
        self.assertEqual(code.get("geni_code", None), 0) # no error
        self.assertIsInstance(value, str)

    def runTest(self):
        """
        Explicitly call tests in order to be invoked through test suite.
        """
        self.test_get_version()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        arg = sys.argv[1]
    del sys.argv[1:]
    unittest.main(verbosity=0, exit=True)
    print_warnings()
