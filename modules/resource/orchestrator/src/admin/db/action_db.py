#!/usr/bin/env python
import sys
import os
import argparse
import pymongo


class CommandMgr(object):
    TABLES = {
        "domain.routing":
            pymongo.MongoClient().felix_ro.domain.routing,
        "resource.com.node":
            pymongo.MongoClient().felix_ro.resource.com.node,
        "resource.com.link":
            pymongo.MongoClient().felix_ro.resource.com.link,
        "resource.of.node":
            pymongo.MongoClient().felix_ro.resource.of.node,
        "resource.of.link":
            pymongo.MongoClient().felix_ro.resource.of.link,
        "resource.se.link":
            pymongo.MongoClient().felix_ro.resource.se.link,
        "resource.se.node":
            pymongo.MongoClient().felix_ro.resource.se.node,
        "resource.tn.link":
            pymongo.MongoClient().felix_ro.resource.tn.link,
        "resource.tn.node":
            pymongo.MongoClient().felix_ro.resource.tn.node,
        "topology.slice":
            pymongo.MongoClient().felix_ro.topology.slice,
        "topology.slice.sdn":
            pymongo.MongoClient().felix_ro.topology.slice.sdn,
        "scheduler.jobs":
            pymongo.MongoClient().felix_ro.scheduler.jobs,
    }

    def __select(self, table, name):
        print "\n\n" + "(RO) %s has %d rows\n" % (name, table.count())
        for row in table.find():
            print "%s" % (row)

    def __delete(self, table, name):
        table.remove()
        print "\n\n" + "Deleted all rows of (RO) %s" % (name)

    def list_tables(self):
        print "\n\nManaged Tables: %s\n\n" % CommandMgr.TABLES.keys()

    def select_routing_table(self):
        self.__select(CommandMgr.TABLES["domain.routing"],
                      "domain.routing")

    def select_ofdatapath_table(self):
        self.__select(CommandMgr.TABLES["resource.of.node"],
                      "resource.of.node")

    def select_oflink_table(self):
        self.__select(CommandMgr.TABLES["resource.of.link"],
                      "resource.of.link")

    def delete_routing_table(self):
        self.__delete(CommandMgr.TABLES["domain.routing"],
                      "domain.routing")

    def delete_ofdatapath_table(self):
        self.__delete(CommandMgr.TABLES["resource.of.node"],
                      "resource.of.node")

    def delete_oflink_table(self):
        self.__delete(CommandMgr.TABLES["resource.of.link"],
                      "resource.of.link")

    def delete_all_tables(self):
        for table, mongo_table in CommandMgr.TABLES.items():
            self.__delete(mongo_table, table)


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
                                      'select_ofdatapath_table',
                                      'select_oflink_table',
                                      'delete_routing_table',
                                      'delete_ofdatapath_table',
                                      'delete_oflink_table',
                                      'delete_all_tables'],
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
        elif args_.action == 'select_ofdatapath_table':
            CommandMgr().select_ofdatapath_table()
        elif args_.action == 'select_oflink_table':
            CommandMgr().select_oflink_table()
        elif args_.action == 'delete_routing_table':
            CommandMgr().delete_routing_table()
        elif args_.action == 'delete_ofdatapath_table':
            CommandMgr().delete_ofdatapath_table()
        elif args_.action == 'delete_oflink_table':
            CommandMgr().delete_oflink_table()
        elif args_.action == 'delete_all_tables':
            CommandMgr().delete_all_tables()

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
