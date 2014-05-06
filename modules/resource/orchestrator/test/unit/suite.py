#!/usr/bin/env python

import unittest2 as unittest
import sys
sys.path.insert(0, "../../src")

from geni.v3.test_api import TestGENIv3API

def testing_suite():
    """
    Explicitely add unit tests to the suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestGENIv3API())
    return suite

def main():
    runner = unittest.TextTestRunner()
    test_suite = testing_suite()
    # Run test suite (aggregation of unit tests)
    test = runner.run(test_suite)
    # Retrieve errors
    test_errors = len(test.errors)
    test_failures = len(test.failures)
    # Return code for exiting program with it
    test_result = True if test_errors + test_failures == 0 else False
    return test_result

if __name__ == '__main__':
    # sys.exit with code to notify Jenkins about validity (or not) of tests
    test_result = main()
    # Inverse logic for tests => 0: OK, 1: ERROR
    test_result = int(not(test_result))
    print test_result
    sys.exit(test_result)
