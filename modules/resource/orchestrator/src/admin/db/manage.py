#!/usr/bin/env python

import argparse
import ast
import os
import pymongo
import sys

path = os.path.abspath(__file__)
path = path.split("/")
path = "/".join(path[:-3])
sys.path.append(path)

from core.config import ConfParser


class GenericCommand:
    def __init__(self):
        self.__active = False

    def activate(self):
        self.__active = True

    def isCompleted(self):
        if not self.__active:
            raise AttributeError("Command is NOT active!")

        self.validate()

    def validate(self):
        raise Exception("Validate method is NOT implemented!")

    def execute(self):
        raise Exception("Execute method is NOT implemented!")


class RoutingTableCommand(GenericCommand):

    def __init__(self):
        GenericCommand.__init__(self)
        self.type_ = None
        self.addr_ = None
        self.port_ = None
        self.protocol_ = None
        self.endpoint_ = None
        self.user_ = None
        self.password_ = None
        self.am_type_ = None
        self.am_version_ = None
        self.config = ConfParser("ro.conf")
        self.master_ro = self.config.get("master_ro")
        self.mro_enabled = ast.literal_eval(self.master_ro.get("mro_enabled"))

    def __get_table(self, table_name):
        db_name = "felix_ro"
        if self.mro_enabled:
            db_name = "felix_mro"
        return getattr(getattr(pymongo.MongoClient(), db_name), table_name)

    def updateType(self, type_):
        self.type_ = type_

    def updateAddress(self, address_):
        self.addr_ = address_

    def updatePort(self, port_):
        self.port_ = port_

    def updateProtocol(self, protocol_):
        self.protocol_ = protocol_

    def updateEndpoint(self, endpoint_):
        self.endpoint_ = endpoint_

    def updateUser(self, user_):
        self.user_ = user_

    def updatePassword(self, password_):
        self.password_ = password_

    def updateAMType(self, am_type_):
        self.am_type_ = am_type_

    def updateAMVersion(self, am_version_):
        self.am_version_ = am_version_

    def checkAllNone(self):
        if self.type_ is not None:
            raise AttributeError("Type argument is NOT allowed!")

        if self.addr_ is not None:
            raise AttributeError("Address argument is NOT allowed!")

        if self.port_ is not None:
            raise AttributeError("Port argument is NOT allowed!")

    def getTable(self):
        db_name = "felix_ro"
        if self.mro_enabled:
            db_name = "felix_mro"
        return getattr(getattr(pymongo.MongoClient(), db_name), "domain.routing")


class Dump(RoutingTableCommand):
    def validate(self):
        self.checkAllNone()

    def __dump_table(self, table, table_name):
        print "(RO) %s has %s rows\n" % (table_name, table.count(),)

        for row_ in table.find():
            print "%s" % (row_,)

    def execute(self):
        self.__dump_table(self.getTable(), "domain.routing")
#        self.__dump_table(pymongo.MongoClient().felix_mro.GeneralInfoTable,
#                          "GeneralInfoTable")

    def helpMessage(self):
        return "dump" + "\n\tGet a dump of the mongoDB db"


class DeleteAll(RoutingTableCommand):
    def validate(self):
        self.checkAllNone()

    def execute(self):
        table_ = self.getTable()
        table_.remove()

        print "(RO) domain.routing delete all rows\n"

    def helpMessage(self):
        return "delete_all" + "\n\tDelete all entries of the mongoDB db"


class AddRouteEntry(RoutingTableCommand):
    def validate(self):
        if self.type_ is None:
            raise AttributeError("Type argument is NOT specified!")

        if self.addr_ is None:
            raise AttributeError("Address argument is NOT specified!")

        if self.port_ is None:
            raise AttributeError("Port argument is NOT specified!")

    def execute(self):
        table_ = self.getTable()

        row_ = {"type": self.type_,
                "address": self.addr_,
                "port": self.port_,
                "protocol": self.protocol_,
                "endpoint": self.endpoint_,
                "user": self.user_,
                "password": self.password_,
                "am_type": self.am_type_,
                "am_version": self.am_version_}

        row_id_ = table_.insert(row_)
        print "(RO) domain.routing insert row: %s\n" % (row_id_,)

    def helpMessage(self):
        return "add_route_entry -t <type> -a <address> -p <port>" +\
               " [--protocol <protocol] [--endpoint <endpoint>]" +\
               " [--user <username>] [--password <password>]" +\
               " [--am_type <type>] [--am_version <version>]" +\
               "\n\tAdd a new entry in the mongoDB db"


class DelRouteEntry(RoutingTableCommand):
    def validate(self):
        if self.type_ is None and\
           self.addr_ is None and\
           self.port_ is None:
            raise AttributeError("You MUST specify at least 1 arg " +
                                 "(type or address or port)!")

    def execute(self):
        table_ = self.getTable()

        row_ = {}
        if self.type_ is not None:
            row_["type"] = self.type_

        if self.addr_ is not None:
            row_["address"] = self.addr_

        if self.port_ is not None:
            row_["port"] = self.port_

        table_.remove(row_)
        print "(RO) domain.routing delete row: %s\n" % (row_,)

    def helpMessage(self):
        return "delete_route_entry [-t <type>] [-a <address>] [-p <port>]" +\
               "\n\tDelete an entry(/ies)in the mongoDB db"


#class AddGeneralInfoEntry(GenericCommand):
#    def __init__(self):
#        GenericCommand.__init__(self)
#        self.domain_ = None
#
#    def updateDomain(self, value):
#        self.domain_ = value
#
#    def validate(self):
#        if self.domain_ is None:
#            raise AttributeError("Domain argument is NOT specified!")
#
#    def execute(self):
#        table_ = pymongo.MongoClient().felix_mro.GeneralInfoTable
#
#        row_ = {"domain": self.domain_}
#
#        row_id_ = table_.insert(row_)
#        print "(RO) GeneralInfoTable insert row: %s\n" % (row_id_,)
#
#    def helpMessage(self):
#        return "add_general-info_entry [--domain <id>]" +\
#               "\n\tAdd a general-info entry in the mongoDB db"


commands = {"dump": Dump(),
            "delete_all": DeleteAll(),
            "add_route_entry": AddRouteEntry(),
            "delete_route_entry": DelRouteEntry(),}
#            "add_general-info_entry": AddGeneralInfoEntry()}


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

    def updateProtocol(self, key, value):
        commands[key].updateProtocol(value)

    def updateEndpoint(self, key, value):
        commands[key].updateEndpoint(value)

    def updateUser(self, key, value):
        commands[key].updateUser(value)

    def updatePassword(self, key, value):
        commands[key].updatePassword(value)

    def updateAMType(self, key, value):
        commands[key].updateAMType(value)

    def updateAMVersion(self, key, value):
        commands[key].updateAMVersion(value)

    def updateDomain(self, key, value):
        commands[key].updateDomain(value)

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
        print "Usage:\n"
        for (_, value) in commands.items():
            print value.helpMessage() + "\n"


class CmdConsume(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values == "?":
            CmdManager.helpMessage()
            sys.exit(0)

        if not CmdManager.find(values):
            print "UNMANAGED command %s" % (values,)
            sys.exit(False)

        CmdManager.activate(values)
        setattr(namespace, self.dest, values)


def main(argv=None):
    if not argv:
        argv = sys.argv

    try:
        bug_reporter_ = "<r.monno@nextworks.it>"
        parser_ = argparse.ArgumentParser(
            description="RO dbmanage",
            epilog="Please, report bugs to " + bug_reporter_,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser_.add_argument("command",
                             action=CmdConsume,
                             help="?=describe how to use every single command")

#        for command in commands.keys():
#            parser_.add_argument(command),
#                             action=CmdConsume,
#                             help="?=%s" % getattr(commands[command],
#                             "helpMessage")())

        parser_.add_argument("-t", help="Set the type of RM")

        parser_.add_argument("-a", help="Set the address of RM")

        parser_.add_argument("-p", help="Set the port of RM")

        parser_.add_argument("--protocol", default="http",
                             help="Set the protocol to communicate with RM")

        parser_.add_argument("--endpoint", default="",
                             help="Set the endpoint of RM")

        parser_.add_argument("--user", default="",
                             help="Set the username to access the RM")

        parser_.add_argument("--password", default="",
                             help="Set the password to access the RM")

        parser_.add_argument("--am_type", default=None,
                             help="Set the AM type")

        parser_.add_argument("--am_version", default=None,
                             help="Set the AM type")

        parser_.add_argument("--domain", default=None,
                             help="Set the Domain name")

        args_ = parser_.parse_args()

    except Exception as ex:
        print "Got an exception parsing flags/options:", ex
        return False

    print "Args=%s" % (args_,)
    comMng_ = CmdManager()

    try:
        if args_.command == "add_general-info_entry":
            comMng_.updateDomain(args_.command, args_.domain)

        else:
            if args_.t is not None:
                comMng_.updateType(args_.command, args_.t)

            if args_.a is not None:
                comMng_.updateAddress(args_.command, args_.a)

            if args_.p is not None:
                comMng_.updatePort(args_.command, args_.p)

            # Arguments with default values
            comMng_.updateProtocol(args_.command, args_.protocol)
            comMng_.updateEndpoint(args_.command, args_.endpoint)
            comMng_.updateUser(args_.command, args_.user)
            comMng_.updatePassword(args_.command, args_.password)
            comMng_.updateAMType(args_.command, args_.am_type)
            comMng_.updateAMVersion(args_.command, args_.am_version)

        comMng_.analyze(args_.command)

    except AttributeError as ex:
        print "MALFORMED command %s" % (args_.command,)
        print "What: %s" % (str(ex),)
        return False

    try:
        comMng_.execute(args_.command)

    except Exception as ex:
        print "RUNTIME exception command %s" % (args_.command,)
        print "What: %s" % (str(ex),)
        return False

    return True

if __name__ == "__main__":
    # update sys-path
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

    sys.exit(main())
