#!/usr/bin/env python
import sys
import os
import argparse
import pymongo


class CommandMgr(object):
    def __select(self, table, name):
        print "\n\n" + "(RO) %s has %d rows\n" % (name, table.count())
        for row in table.find():
            print "%s" % (row)

    def __delete(self, table, name):
        table.remove()
        print "\n\n" + "Deleted all rows of (RO) %s" % (name)

    def list_tables(self):
        print "\n\n" + "Managed Tables: [RoutingTable, OFNodeTable, " +\
              "OFLinkTable]\n\n"

    def select_routing_table(self):
        self.__select(pymongo.MongoClient().felix_ro.RoutingTable,
                      "RoutingTable")

    def select_ofnode_table(self):
        self.__select(pymongo.MongoClient().felix_ro.OFNodeTable,
                      "OFNodeTable")

    def select_oflink_table(self):
        self.__select(pymongo.MongoClient().felix_ro.OFLinkTable,
                      "OFLinkTable")

    def delete_routing_table(self):
        self.__delete(pymongo.MongoClient().felix_ro.RoutingTable,
                      "RoutingTable")

    def delete_ofnode_table(self):
        self.__delete(pymongo.MongoClient().felix_ro.OFNodeTable,
                      "OFNodeTable")

    def delete_oflink_table(self):
        self.__delete(pymongo.MongoClient().felix_ro.OFLinkTable,
                      "OFLinkTable")


def main(argv=None):
    if not argv:
        argv = sys.argv

    try:
        bug_reporter_ = '<r.monno@nextworks.it>'
        parser_ = argparse.ArgumentParser(
            description='RO Read MongoDB tables',
            epilog='Please, report bugs to ' + bug_reporter_,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser_.add_argument('--action',
                             choices=['list_tables',
                                      'select_routing_table',
                                      'select_ofnode_table',
                                      'select_oflink_table',
                                      'delete_routing_table',
                                      'delete_ofnode_table',
                                      'delete_oflink_table'],
                             required=True,
                             help='Make an action on (RO) MongoDB')

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an exception parsing flags/options:', ex
        return False

    print "Args=%s" % (args_,)
    try:
        if args_.action == 'list_tables':
            CommandMgr().list_tables()
        elif args_.action == 'select_routing_table':
            CommandMgr().select_routing_table()
        elif args_.action == 'select_ofnode_table':
            CommandMgr().select_ofnode_table()
        elif args_.action == 'select_oflink_table':
            CommandMgr().select_oflink_table()
        elif args_.action == 'delete_routing_table':
            CommandMgr().delete_routing_table()
        elif args_.action == 'delete_ofnode_table':
            CommandMgr().delete_ofnode_table()
        elif args_.action == 'delete_oflink_table':
            CommandMgr().delete_oflink_table()

    except Exception as e:
        print "Got an Exception: %s" % (str(e))
        return False
    return True


if __name__ == '__main__':
    # update sys-path
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

    sys.exit(main())
