import pymongo


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db"""
    def __init__(self):
        self.table_ = pymongo.MongoClient().felix_ro.RoutingTable

    def get_all(self):
        return [row for row in self.table_.find()]
