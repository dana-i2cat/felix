#!/usr/bin/env python

# TODO Convert to unittest, update paths added to syspath, etc

import sys
import os

if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)
        sys.path.insert(0, "../../../../../../src")

from rspecs.commons import validate
from rspecs.serm.request_parser import SERMv3RequestParser
from rspecs.serm.manifest_parser import SERMv3ManifestParser


def in_validate(rspec):
    (result, error) = validate(rspec)
    if not result:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"


def main(argv=None):
    if not argv:
        argv = sys.argv

    print 'Start the test environment'
    print '=== SERMv3RequestParser: request_rspec_example.xml ==='
    rspec = SERMv3RequestParser("request_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print '=== SERMv3RequestParser: request_rspec_example-1.xml ==='
    rspec = SERMv3RequestParser("request_rspec_example-1.xml")
    in_validate(rspec.get_rspec())

    print '=== SERMv3ManifestParser: manifest_rspec_example.xml ==='
    rspec = SERMv3ManifestParser("manifest_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print 'Bye Bye...'
    return True


if __name__ == '__main__':
    sys.exit(main())
