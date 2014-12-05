#!/usr/bin/env python

# TODO Convert to unittest, update paths added to syspath, etc

import sys
import os

if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)
        pref = "../../../../../../src"
        sys.path.insert(0, pref)
        sys.path.insert(0, pref + "/delegate/geni/v3/rspecs/")
        sys.path.insert(0, pref + "/delegate/geni/v3/rspecs/tnrm")

from commons import validate
from manifest_parser import TNRMv3ManifestParser


def main(argv=None):
    if not argv:
        argv = sys.argv

    print 'Start the test environment'
    print '=== TNRMv3ManifestParser ==='
    rspec = TNRMv3ManifestParser("manifest_rspec_example.xml")

    (result, error) = validate(rspec.get_rspec())
    if not result:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"

    print 'Bye Bye...'
    return True

if __name__ == '__main__':
    sys.exit(main())
