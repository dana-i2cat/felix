#from utils import geniv3_handler_tools
import sys
# Adding paths to locate modules within the "src" package
sys.path.insert(0, "../../../../src")

from core.utils import calls as call_utils
from extensions.geni.util import cred_util
from extensions.sfa.trust import gid

# Adding path to locate "utils" module within the "test" package
sys.path.insert(0, "../../..")

from utils import testcase


class TestListResources(testcase.TestCase):
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
        (text, self.user_credential) = call_utils.getusercred(geni_api = 3)

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
            "geni_compressed": False, # True => seems to return a base64 compressed and encoded value
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
            "geni_api_versions": {"type": dict, "value": {"3": "/xmlrpc/geni/3/"}},
            "geni_single_allocation": {"type": bool},
            "geni_allocate": {"type": str},
        }
        self.geni_params = [
            self.geni_v3_credentials,
            self.geni_v3_options,
        ]
    
    def tearDown(self):
        pass
    
    def test_should_list_resources_expected_type(self):
        code, value, output = call_utils.handler_call("ListResources", self.geni_params)
        self.assertIsInstance(value, str)

if __name__ == '__main__':
    # Allows to run in stand-alone mode
    testcase.main()
