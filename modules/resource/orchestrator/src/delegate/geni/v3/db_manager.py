import pymongo


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db"""
    def __init__(self):
        pass

    def get_configured_peers(self):
        self.routing_table_ = pymongo.MongoClient().felix_ro.RoutingTable
        return [row for row in self.routing_table_.find()]
