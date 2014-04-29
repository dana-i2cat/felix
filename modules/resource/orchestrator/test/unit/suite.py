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

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    test_suite = testing_suite()
    # Run test suite (aggregation of unit tests)
    runner.run(test_suite)
