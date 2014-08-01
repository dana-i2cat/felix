from utils import geniv3_handler_tools

import datetime
import os
import sys
#import unittest
import unittest2 as unittest

# Adding paths to locate modules from other packages
sys.path.insert(0, "../../../../src")
from handler.geni.v3.extensions.geni.util import cred_util
from handler.geni.v3.extensions.sfa.trust import gid

# TODO: Get the cert_root from the configuration settings
cert_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../cert"))


class TestGetVersion(unittest.TestCase):
    """ Testing very basic behaviour to see 
        whether the handler is able to respond
        with error_results or success_results  
    """
    @classmethod
    def setUp(self):
        """
        Sets up environment, e.g. asking for credentials.
        """
        # Contact GCH for it by passing the certificate. Equivalent to 'omni.py getusercred'
        (text, self.user_credential) = geniv3_handler_tools.getusercred(geni_api = 3)

        self.geni_v3_credentials = [{
            "geni_type": "geni_sfa",
            "geni_value": self.user_credential["geni_value"],
        }]
        # Any AM is required to honor the following options
        self.geni_v3_options = {
            "geni_available": True,
            # XXX: it should say 'compressed' (as for GENIv3), not 'compress' (as in AMsoil)
            # http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#ListResources
            #"geni_compressed": False,
            "geni_compress": False, # True => seems to return a base64 compressed and encoded value
            "geni_rspec_version": {
                "type": "geni",
                "version": "3",
            }
        }
        self.geni_options_expected_key_info = {
            "geni_credential_types": {"type": dict, "value": {"geni_version": "3", "geni_type": "geni_sfa"}},
            "geni_ad_rspec_versions": {"type": list},
            "geni_request_rspec_versions": {"type": list},
            "geni_api": {"type": str, "value": "3"},
            "geni_api_versions": {"type": dict, "value": {"3": "/geni/3"}},
            "geni_single_allocation": {"type": bool},
            "geni_allocate": {"type": str},
        }
        self.geni_params = [
            self.geni_v3_credentials,
            self.geni_v3_options,
        ]
    
    def tearDown(self):
        pass
    
    def test_should_get_version_expected_type(self):
        code, value, output = geniv3_handler_tools.handler_call("GetVersion")
        self.assertIsInstance(value, dict)
    
    def test_should_get_version_expected_keys(self):
        code, value, output = geniv3_handler_tools.handler_call("GetVersion")
        self.assertIsInstance(value, dict)
        # Ensure keys from returned dictionary
        for expected_key in self.geni_options_expected_key_info:
            self.assertIn(expected_key, value)
    
    def test_should_get_version_keys_expected_type(self):
        code, value, output = geniv3_handler_tools.handler_call("GetVersion")
        self.assertIsInstance(value, dict)
        # Ensure type of keys from returned dictionary
        for expected_key in self.geni_options_expected_key_info:
            expected_key_type = self.geni_options_expected_key_info.get(expected_key).get("type")
            if expected_key_type:
                self.assertIsInstance(value.get(expected_key), expected_key_type)
    
    def test_should_get_version_keys_expected_value(self):
        code, value, output = geniv3_handler_tools.handler_call("GetVersion")
        self.assertIsInstance(value, dict)
        # Ensure value of keys from returned dictionary
        for expected_key in self.geni_options_expected_key_info:
            expected_key_value = self.geni_options_expected_key_info.get(expected_key).get("value")
            if expected_key_value:
                self.assertEquals(expected_key_value, value.get(expected_key))
    
    def runTest(self):
        """
        Explicitly call tests in order to be invoked through test suite.
        """
        # Dynamic retrieval of tests in module (methods starting with "test_")
        existing_tests = filter(lambda x: x.startswith("test_"), dir(self))
        for existing_test in existing_tests:
            # Invoke each test method
            getattr(self, existing_test)()

def main():
    test = unittest.main(verbosity=2, exit=False)
    # Retrieve errors
    #test_passed = test.result.wasSuccessful()
    #test_total = test.result.testsRun
    test_errors = len(test.result.errors)
    test_failures = len(test.result.failures)
    # Return code for exiting program with it
    test_result = True if test_errors + test_failures == 0 else False
    return test_result

if __name__ == '__main__':
    if len(sys.argv) == 2:
        arg = sys.argv[1]
    del sys.argv[1:]
    # sys.exit with code to notify Jenkins about validity (or not) of tests
    test_result = main()
    # Inverse logic for tests => 0: OK, 1: ERROR
    test_result = int(not(test_result))
    print test_result
    sys.exit(test_result)
