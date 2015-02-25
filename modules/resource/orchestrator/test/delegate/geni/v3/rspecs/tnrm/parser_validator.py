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
from rspecs.tnrm.advertisement_parser import TNRMv3AdvertisementParser
from rspecs.tnrm.request_parser import TNRMv3RequestParser
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser


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
    print '=== TNRMv3AdvertisementParser ==='
    rspec = TNRMv3AdvertisementParser("adv_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print '=== TNRMv3RequestParser ==='
    rspec = TNRMv3RequestParser("request_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print '=== TNRMv3ManifestParser ==='
    rspec = TNRMv3ManifestParser("manifest_rspec_example.xml")
    in_validate(rspec.get_rspec())

    nodes = rspec.nodes()
    print "Nodes=%s" % nodes

    print 'Bye Bye...'
    return True


if __name__ == '__main__':
    sys.exit(main())
