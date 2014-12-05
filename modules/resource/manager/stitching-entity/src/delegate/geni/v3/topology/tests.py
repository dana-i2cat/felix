#!/usr/bin/env python
import sys

sys.path.insert(0, "../../../../")

import topology
import algorithm


def main():
    print "Start the algorithm test"
    AM = algorithm.AlgorithmManager()

    # Add some nodes
    island1_cr_1 = topology.CNode("felix:EU:i2cat:IT-R:server-1")
    island1_cr_2 = topology.CNode("felix:EU:i2cat:IT-R:server-2")
    island1_cr_3 = topology.CNode("felix:EU:i2cat:IT-R:server-3")
    island1_tr_1 = topology.TNode("felix:EU:i2cat:TN-R:stp-1")

    island2_cr_1 = topology.CNode("felix:EU:psnc:IT-R:server-1")
    island2_cr_2 = topology.CNode("felix:EU:psnc:IT-R:server-2")
    island2_tr_1 = topology.TNode("felix:EU:psnc:TN-R:stp-1")

    island3_cr_1 = topology.CNode("felix:JP:kddi:IT-R:server-1")
    island3_cr_2 = topology.CNode("felix:JP:kddi:IT-R:server-2")
    island3_cr_3 = topology.CNode("felix:JP:kddi:IT-R:server-3")
    island3_tr_1 = topology.TNode("felix:JP:kddi:TN-R:stp-1")

    AM.add_nodes([island1_cr_1, island1_cr_2, island1_cr_3, island1_tr_1,
                  island2_cr_1, island2_cr_2, island2_tr_1,
                  island3_cr_1, island3_cr_2, island3_cr_3, island3_tr_1])

    print "--->Nodes: %s" % AM.str_nodes()

    # Add the links
    AM.add_bidir_link(island1_cr_1, island1_tr_1)
    AM.add_bidir_link(island1_cr_2, island1_tr_1)
    AM.add_bidir_link(island1_cr_3, island1_tr_1)

    AM.add_bidir_link(island2_cr_1, island2_tr_1)
    AM.add_bidir_link(island2_cr_2, island2_tr_1)

    AM.add_bidir_link(island3_cr_1, island3_tr_1)
    AM.add_bidir_link(island3_cr_2, island3_tr_1)
    AM.add_bidir_link(island3_cr_3, island3_tr_1)

    AM.add_unidir_link(island1_tr_1, island2_tr_1)
    AM.add_unidir_link(island2_tr_1, island3_tr_1)

    print "--->Links: %s" % AM.str_links()

    # Path Computation (no exception!)
    try:
        path = AM.run_djikstra(island1_cr_1, island3_cr_3)
        print "--->Path(%s->%s): %s" % (island1_cr_1, island3_cr_3, path,)

    except Exception as e:
        print "--->(failure) Exception: %s" % (str(e),)

    # Path Computation (it must raise an exception!)
    try:
        path = AM.run_djikstra(island3_cr_2, island1_cr_3)
        print "--->Path(%s->%s): %s" % (island3_cr_2, island1_cr_3, path,)

    except Exception as e:
        print "--->(success) Exception: %s" % (str(e),)

    print 'Algorithm test successfully ended...'
    return True


if __name__ == '__main__':
    sys.exit(main())
