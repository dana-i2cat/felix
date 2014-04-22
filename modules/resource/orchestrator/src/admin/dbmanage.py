#!/usr/bin/env python

import sys
import os
import argparse
import pymongo


class GenericCommand:
    def __init__(self):
        self.__active = False

    def activate(self):
        self.__active = True

    def isCompleted(self):
        if not self.__active:
            raise AttributeError('Command is NOT active!')

        self.validate()

    def validate(self):
        raise Exception('Validate method is NOT implemented!')

    def execute(self):
        raise Exception('Execute method is NOT implemented!')


class RoutingTableCommand(GenericCommand):
    def __init__(self):
        GenericCommand.__init__(self)
        self.type_ = None
        self.addr_ = None
        self.port_ = None

    def updateType(self, type_):
        self.type_ = type_

    def updateAddress(self, address_):
        self.addr_ = address_

    def updatePort(self, port_):
        self.port_ = port_

    def checkAllNone(self):
        if self.type_ is not None:
            raise AttributeError('Type argument is NOT allowed!')

        if self.addr_ is not None:
            raise AttributeError('Address argument is NOT allowed!')

        if self.port_ is not None:
            raise AttributeError('Port argument is NOT allowed!')

    def getTable(self):
        client_ = pymongo.MongoClient()
        felix_ro_ = client_.felix_ro
        return felix_ro_.RoutingTable


class Dump(RoutingTableCommand):
    def validate(self):
        self.checkAllNone()

    def execute(self):
        table_ = self.getTable()

        print '(RO) RoutingTable has %s rows\n' % (table_.count(),)

        for row_ in table_.find():
            print '%s' % (row_,)

    def helpMsg(self):
        return 'dump' + '\n\tGet a dump of the mongoDB db'


class DeleteAll(RoutingTableCommand):
    def validate(self):
        self.checkAllNone()

    def execute(self):
        table_ = self.getTable()
        table_.remove()

        print '(RO) RoutingTable delete all rows\n'

    def helpMsg(self):
        return 'delete_all' + '\n\tDelete all entries of the mongoDB db'


class AddRouteEntry(RoutingTableCommand):
    def validate(self):
        if self.type_ is None:
            raise AttributeError('Type argument is NOT specified!')

        if self.addr_ is None:
            raise AttributeError('Address argument is NOT specified!')

        if self.port_ is None:
            raise AttributeError('Port argument is NOT specified!')

    def execute(self):
        table_ = self.getTable()

        row_ = {'type': self.type_,
                'address': self.addr_,
                'port': self.port_}

        row_id_ = table_.insert(row_)
        print '(RO) RoutingTable insert row: %s\n' % (row_id_,)

    def helpMsg(self):
        return 'add_route_entry -t <type> -a <address> -p <port>' +\
               '\n\tAdd a new entry in the mongoDB db'


class DelRouteEntry(RoutingTableCommand):
    def validate(self):
        if self.type_ is None and\
           self.addr_ is None and\
           self.port_ is None:
            raise AttributeError('You MUST specify at least 1 arg ' +
                                 '(type or address or port)!')

    def execute(self):
        table_ = self.getTable()

        row_ = {}
        if self.type_ is not None:
            row_['type'] = self.type_

        if self.addr_ is not None:
            row_['address'] = self.addr_

        if self.port_ is not None:
            row_['port'] = self.port_

        table_.remove(row_)
        print '(RO) RoutingTable delete row: %s\n' % (row_,)

    def helpMsg(self):
        return 'delete_route_entry [-t <type>] [-a <address>] [-p <port>]' +\
               '\n\tDelete an entry(/ies)in the mongoDB db'

commands = {'dump': Dump(),
            'delete_all': DeleteAll(),
            'add_route_entry': AddRouteEntry(),
            'delete_route_entry': DelRouteEntry()}


class CmdManager:
    def analyze(self, key):
        commands[key].isCompleted()

    def execute(self, key):
        commands[key].execute()

    def updateType(self, key, value):
        commands[key].updateType(value)

    def updateAddress(self, key, value):
        commands[key].updateAddress(value)

    def updatePort(self, key, value):
        commands[key].updatePort(value)

    @staticmethod
    def find(key):
        if key not in commands:
            return False
        return True

    @staticmethod
    def activate(key):
        commands[key].activate()

    @staticmethod
    def helpMessage():
        print 'Usage:\n'
        for (_, value) in commands.items():
            print value.helpMsg() + '\n'


class CmdConsume(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values == '?':
            CmdManager.helpMessage()
            sys.exit(0)

        if not CmdManager.find(values):
            print 'UNMANAGED command %s' % (values,)
            sys.exit(False)

        CmdManager.activate(values)
        setattr(namespace, self.dest, values)


def main(argv=None):
    if not argv:
        argv = sys.argv

    try:
        bug_reporter_ = '<r.monno@nextworks.it>'
        parser_ = argparse.ArgumentParser(
            description='RO dbmanage',
            epilog='Please, report bugs to ' + bug_reporter_,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser_.add_argument('command',
                             action=CmdConsume,
                             help='?=describe how to use every single command')

        parser_.add_argument('-t', help='Set the type of RM')

        parser_.add_argument('-a', help='Set the address of RM')

        parser_.add_argument('-p', help='Set the port of RM')

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an exception parsing flags/options:', ex
        return False

    comMng_ = CmdManager()

    try:
        if args_.t is not None:
            comMng_.updateType(args_.command, args_.t)

        if args_.a is not None:
            comMng_.updateAddress(args_.command, args_.a)

        if args_.p is not None:
            comMng_.updatePort(args_.command, args_.p)

        comMng_.analyze(args_.command)

    except AttributeError as ex:
        print 'MALFORMED command %s' % (args_.command,)
        print 'What: %s' % (str(ex),)
        return False

    try:
        comMng_.execute(args_.command)

    except Exception as ex:
        print 'RUNTIME exception command %s' % (args_.command,)
        print 'What: %s' % (str(ex),)
        return False

    return True

if __name__ == '__main__':
    # update sys-path
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

    sys.exit(main())
