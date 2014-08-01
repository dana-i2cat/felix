#!/usr/bin/env python

# TODO Convert to unittest, update paths added to syspath, etc

import sys
import os

if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)
        sys.path.insert(0, "../../../../..")

from sdn_commons import OpenFlowNode, validate
from sdn_advertisement_formatter import OFv3AdvertisementFormatter
from sdn_advertisement_parser import OFv3AdvertisementParser


def main(argv=None):
    if not argv:
        argv = sys.argv

    print 'Start the test environment'
    print '=== OFv3AdvertisementFormatter ==='

    rspec = OFv3AdvertisementFormatter()
    prefix = "urn:publicid:IDN+openflow:foam:foam.gpolab.bbn.com+"
    of_node = OpenFlowNode(prefix + "datapath:06:d6:00:24:a8:c4:b9:00",
                           prefix + "authority+am",
                           "06:d6:00:24:a8:c4:b9:00",
                           "false",
                           "true")
    of_node.add_port(3, "GBE0/3")
    of_node.add_port(5, "GBE0/5")
    of_node.add_port(9, "GBE0/9")
    of_node.add_port(20, "GBE0/20")
    of_node.add_port(22, "GBE0/22")
    of_node.add_port(666)
    rspec.datapath(of_node)

    of_node = OpenFlowNode(prefix + "datapath:06:d6:00:24:a8:c4:cc:ff",
                           prefix + "authority+am",
                           "06:d6:00:24:a8:c4:cc:ff",
                           "false",
                           "true")
    of_node.add_port(11, "pippo")
    of_node.add_port(45, "pluto")
    rspec.datapath(of_node)

    print rspec
    (result, error) = validate(rspec.get_rspec())
    if result != True:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"

    print '=== OFv3RequestParser ==='
    rspec = OFv3AdvertisementParser("sdn_adv_rspec_example.xml")

    (result, error) = validate(rspec.get_rspec())
    if result != True:
        print "Validation failure: %s" % error
    else:
        print "Validation success!"

    nodes = rspec.nodes()
    print "Nodes(%d)=%s" % (len(nodes), nodes)

    ofnodes = rspec.ofnodes()
    print "OFNodes(%d)=%s" % (len(ofnodes), ofnodes)

    for ofn in ofnodes:
        ofnode = ofn.get("ofnode")
        print "DPID=%s" % ofnode.dpid
        print "PORTS=%s" % ofnode.ports

    print 'Bye Bye...'
    return True

if __name__ == '__main__':
    sys.exit(main())
