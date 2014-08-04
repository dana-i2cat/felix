import sys

# Adding paths to locate modules within the "src" package
sys.path.insert(0, "../../../../src")
# Adding path to locate "utils" module within the "test" package
sys.path.insert(0, "../../..")
import testcase

class TestSample(testcase.FelixTestCase):
    """
    IMPORTANT:
    Test module must start with "test_" (e.g. test_getversion.py)
    Test class must start with "Test" name (e.g. TestGetVersion)
    
    Add test description here. 
    """
    @classmethod
    def setUp(self):
        """
        Fill with needed initialisations.
        """
        pass
    
    def tearDown(self):
        """
        Fill with any removal, delete, etc.
        """
        pass
    
    def test_do_some_action(self):
        """
        Fill with proper checks.
        """
        pass

def main():
    # Allows to run in stand-alone mode
    return testcase.main()

if __name__ == '__main__':
    # Allows to run in stand-alone mode
    testcase.invoke_main()
