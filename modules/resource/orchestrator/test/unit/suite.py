#!/usr/bin/env python

import unittest2 as unittest

from geni.v3.computing_rm import TestComputingRM

def testing_suite():
    suite = unittest.TestSuite()
    suite.addTest (TestComputingRM())
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    test_suite = testing_suite()
    # Run test suite (aggregation of unit tests)
    runner.run(test_suite)
