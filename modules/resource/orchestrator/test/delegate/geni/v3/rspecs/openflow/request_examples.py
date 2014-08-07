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
        sys.path.insert(0, pref + "/delegate/geni/v3/rspecs/openflow")

from commons import Datapath, Match, CONTROLLER_TYPE_PRIMARY, validate
from request_formatter import OFv3RequestFormatter
from request_parser import OFv3RequestParser


def main(argv=None):
    if not argv:
        argv = sys.argv

    print 'Start the test environment'
    print '=== OFv3RequestFormatter ==='

    rspec = OFv3RequestFormatter()
    rspec.sliver(description="My GENI experiment",
                 ref="http://www.geni.net",
                 email="user@geni.net")
    rspec.controller(url="tcp:myctrl.example.net:9933",
                     type=CONTROLLER_TYPE_PRIMARY)
    rspec.group(name="mygrp")

    # first datapath
    prefix = "urn:publicid:IDN+openflow:foam:uxmal.gpolab.bbn.com+"
    dp = Datapath(prefix + "datapath:06:a4:00:12:e2:b8:a5:d0",
                  prefix + "authority+am",
                  "06:a4:00:12:e2:b8:a5:d0")
    dp.add_port(7, "GBE0/7")
    dp.add_port(20, "GBE0/20")
    rspec.datapath("mygrp", dp)

    # second datapath
    dp = Datapath(prefix + "datapath:06:af:00:24:a8:c4:b9:00",
                  prefix + "authority+am",
                  "06:af:00:24:a8:c4:b9:00")
    dp.add_port(50, "26")
    dp.add_port(71, "47")
    dp.add_port(65534)
    rspec.datapath("mygrp", dp)

    # first match
    m = Match()
    m.add_use_group("mygrp")
    m.add_use_group("pippuzzo")
    m.set_packet(dl_type="0x800", nw_src="10.1.1.0/24",
                 nw_proto="6, 17", tp_src="80")
    rspec.match(m)

    # second match
    m = Match()
    m.add_use_group("mygrp")
    m.add_datapath(dp)
    m.add_datapath(dp)
    m.set_packet(dl_type="0x800", nw_dst="10.1.1.0/24",
                 nw_proto="617", tp_dst="8080")
    rspec.match(m)

    print rspec
    (result, error) = validate(rspec.get_rspec())
    if result is not True:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"

    print '=== OFv3RequestParser ==='
    rspec = OFv3RequestParser("request_rspec_example.xml")

    (result, error) = validate(rspec.get_rspec())
    if result is not True:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"

    sliver = rspec.sliver()
    print "Sliver=%s" % sliver

    controllers = rspec.controllers()
    print "Controllers=%s" % controllers

    groups = rspec.groups()
    print "Groups=%s" % groups

    datapaths = rspec.datapaths(groups[0]["name"])
    print "Group=%s, Datapath=%s" % (groups[0]["name"], datapaths)

    matches = rspec.matches()
    print "Matches=%s" % matches

    print 'Bye Bye...'
    return True

if __name__ == '__main__':
    sys.exit(main())
