#!/usr/bin/env python

#import unittest
import unittest2 as unittest
import sys

sys.path.insert(0, "../..")
from tools import *

arg = None

def handler_call(method_name, params=[], user_name="alice"):
    if arg in ["-v", "--verbose"]:
        verbose = True
    else:
        verbose = False
    return api_call(method_name, "geni/3/computing", params=params, user_name=user_name, verbose=verbose)

class TestComputingRM(unittest.TestCase):

    @classmethod
    def setUp(self):
        pass

    def test_get_version(self):
        """
        Test 'get_version' method.

        Check result for various valid/required fields.
        """
        code, value, output = handler_call('GetVersion')
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
        self.assertEquals(value["geni_api_versions"].values()[0], "/geni/3/computing")
        self.assertEquals(value["geni_api"], "3")

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
