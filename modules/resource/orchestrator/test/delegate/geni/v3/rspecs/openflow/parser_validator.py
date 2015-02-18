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
from rspecs.openflow.advertisement_parser import OFv3AdvertisementParser
from rspecs.openflow.request_parser import OFv3RequestParser
from rspecs.openflow.manifest_parser import OFv3ManifestParser


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
    print '=== OFv3AdvertisementParser ==='
    rspec = OFv3AdvertisementParser("adv_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print '=== OFv3RequestParser ==='
    rspec = OFv3RequestParser("request_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print '=== OFv3ManifestParser ==='
    rspec = OFv3ManifestParser("manifest_rspec_example.xml")
    in_validate(rspec.get_rspec())

    print 'Bye Bye...'
    return True


if __name__ == '__main__':
    sys.exit(main())
