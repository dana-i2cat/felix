from utils import geniv3_handler_tools
import sys
# Adding paths to locate modules within the "src" package
sys.path.insert(0, "../../../../src")
from handler.geni.v3.extensions.geni.util import cred_util
from handler.geni.v3.extensions.sfa.trust import gid
# Adding path to locate "utils" module within the "test" package
sys.path.insert(0, "../../..")
import testcase


class TestGetVersion(testcase.TestCase):
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

        self.geni_options_expected_key_info = {
            "geni_credential_types": {"type": dict, "value": {"geni_version": "3", "geni_type": "geni_sfa"}},
            "geni_ad_rspec_versions": {"type": list},
            "geni_request_rspec_versions": {"type": list},
            "geni_api": {"type": str, "value": "3"},
            "geni_api_versions": {"type": dict, "value": {"3": "/xmlrpc/geni/3/"}},
            "geni_single_allocation": {"type": bool},
            "geni_allocate": {"type": str},
        }
    
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

if __name__ == '__main__':
    # Allows to run in stand-alone mode
    testcase.main()
