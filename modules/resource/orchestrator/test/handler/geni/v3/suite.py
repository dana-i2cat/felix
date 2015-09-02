#!/usr/bin/env python

#from test_getversion import TestGetVersion
import unittest2 as unittest
import sys
sys.path.insert(0, "../../../src")


def retrieve_tests_in_dir(path = "."):
    import os
    modules_in_package = os.listdir(path)
    # Dynamic retrieval of modules in package (methods starting with "test_")
    existing_tests = filter(lambda x: x.startswith("test_") and x.endswith(".py"), modules_in_package)
    # Remove extension and filter compiled files, etc
    existing_tests = set([ x[:x.index(".")] for x in existing_tests ])
    tests_to_add = dict()
    for existing_test in existing_tests:
        # Import existing test
        imported_existing_test = __import__(existing_test)
        # Retrieve elements within it
        elements_in_module = dir(imported_existing_test)
        # Dynamic retrieval of classes in module (elements starting with "Test")
        elements_in_module = filter(lambda x: x.startswith("Test"), elements_in_module)
        # Retrieve the name of the class in the module
        for element_in_module in elements_in_module:
            tests_to_add[existing_test] = {"class": element_in_module}
    return tests_to_add

def testing_suite():
    """
    Explicitely add unit tests to the suite.
    """
#    suite = unittest.TestSuite()
#    tests_to_add = retrieve_tests_in_dir()
#    for test_to_add in tests_to_add:
#        #print tests_to_add.get(test_to_add).get("class")
#        class_name = tests_to_add.get(test_to_add).get("class")
#        # Equivalent to "from <test_to_add> import <class_name>"
#        class_instance = __import__(test_to_add, globals(), locals(), [class_name], -1)
#        # Retrieve the class itself and invoke it
#        class_instance = getattr(class_instance, class_name)()
#        suite.addTest(class_instance)
#    #suite.addTest(TestGetVersion())
#    return suite

def testing_suites():
    """
    Explicitely add unit tests to the suites.
    """
    suites = list()
    tests_to_add = retrieve_tests_in_dir()
    for test_to_add in tests_to_add:
        class_name = tests_to_add.get(test_to_add).get("class")
        # Equivalent to "from <test_to_add> import <class_name>"
        class_instance = __import__(test_to_add, globals(), locals(), [class_name], -1)
        # Retrieve the class itself
        class_instance = getattr(class_instance, class_name)
        # Load all tests from class (allows verbosity)
        suite = unittest.TestLoader().loadTestsFromTestCase(class_instance)
        suites.append(suite)
    return suites

def main():
    # Say which tests you are running, please
    runner = unittest.TextTestRunner(verbosity=2)
    test_suites = testing_suites()
    # Initially true for AND-like operations
    test_result = True
    test_errors = list()
    test_failures = list()
    for test_suite in test_suites:
        # Run test suite (aggregation of unit tests)
        test = runner.run(test_suite)
        # Retrieve errors
        test_errors.append(len(test.errors))
        test_failures.append(len(test.failures))
        #test_result = True if test_errors + test_failures == 0 else False
    for test_output in zip(test_errors, test_failures):
        # Return code for exiting program with it: 0 (OK), 1 (KO)
        test_result &= True if sum(test_output) == 0 else False
    return test_result

if __name__ == '__main__':
    # sys.exit with code to notify Jenkins about validity (or not) of tests
    test_result = main()
    # Inverse logic for tests => 0: OK, 1: ERROR
    test_result = int(not(test_result))
    print test_result
    sys.exit(test_result)
