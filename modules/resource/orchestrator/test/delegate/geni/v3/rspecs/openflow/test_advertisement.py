import sys
import sys
# Adding paths to locate modules within the "src" package
sys.path.insert(0, "../../../../../../src")
from delegate.geni.v3.rspecs.openflow.commons import Datapath, Match, CONTROLLER_TYPE_PRIMARY
from delegate.geni.v3.rspecs.openflow.request_formatter import OFv3RequestFormatter
from delegate.geni.v3.rspecs.openflow.request_parser import OFv3RequestParser
# Adding path to locate "utils" module within the "test" package
sys.path.insert(0, "../../../../../..")
from test.delegate.geni.v3.rspecs.utils import rspec_validation
from test.utils import testcase


class TestAdvertisement(testcase.FelixTestCase):
    @classmethod
    def setUp(self):
        """
        Sets up environment, e.g. asking for credentials.
        """
        pass
    
    def tearDown(self):
        pass

def main():
    # Allows to run in stand-alone mode
    return testcase.main()

if __name__ == '__main__':
    # Allows to run in stand-alone mode
    testcase.invoke_main()
