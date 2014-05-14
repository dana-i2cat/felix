import pymongo


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db"""
    def __init__(self):
        pass

    def get_configured_peers(self):
        self.routing_table_ = pymongo.MongoClient().felix_ro.RoutingTable
        return [row for row in self.routing_table_.find()]

    def update_am_info(self, object_id, am_type, am_version):
        self.routing_table_ = pymongo.MongoClient().felix_ro.RoutingTable
        self.routing_table_.update({'_id': object_id},
                                   {"$set": {'am_type': am_type,
                                             'am_version': am_version}})
