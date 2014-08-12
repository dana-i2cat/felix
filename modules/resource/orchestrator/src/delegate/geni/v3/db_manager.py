import pymongo
import threading

import core
logger = core.log.getLogger("db-manager")


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db"""
    def __init__(self):
        self.__mutex = threading.Lock()

    def get_configured_peers(self):
        table = pymongo.MongoClient().felix_ro.RoutingTable
        try:
            self.__mutex.acquire()
            return [row for row in table.find()]
        finally:
            self.__mutex.release()

    def update_am_info(self, object_id, am_type, am_version):
        table = pymongo.MongoClient().felix_ro.RoutingTable
        try:
            self.__mutex.acquire()
            table.update({'_id': object_id},
                         {"$set": {'am_type': am_type,
                                   'am_version': am_version}})
        finally:
            self.__mutex.release()

    def store_sdn_nodes(self, values):
        table = pymongo.MongoClient().felix_ro.OFNodeTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    'component_id': v.get('component_id'),
                    'component_manager_id': v.get('component_manager_id'),
                    'dpid': v.get('dpid')})
                if row is None:
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                logger.debug("%s already stored!" % (row.get('_id')))
                m = {}
                if row.get('exclusive') != v.get('exclusive'):
                    m['exclusive'] = v.get('exclusive')
                if row.get('available_now') != v.get('available_now'):
                    m['available_now'] = v.get('available_now')
                if row.get('hardware_type_name')!= v.get('hardware_type_name'):
                    m['hardware_type_name'] = v.get('hardware_type_name')
                if row.get('component_name') != v.get('component_name'):
                    m['component_name'] = v.get('component_name')

                # TODO: missing ports verification!
                if len(m) > 0:
                    table.update({'_id': row.get('_id')},
                                 {"$set": m})
                else:
                    logger.info("(sdn-node) %s already stored!" %\
                                (row.get('_id')))
            return ids
        finally:
            self.__mutex.release()

    def store_sdn_links(self, values):
        table = pymongo.MongoClient().felix_ro.OFLinkTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = None
                if v.get('dstDPID'):
                    row = table.find_one({'srcDPID': v.get('srcDPID'),
                                          'srcPort': v.get('srcPort'),
                                          'dstDPID': v.get('dstDPID'),
                                          'dstPort': v.get('dstPort')})
                elif v.get('dstDevice'):
                    row = table.find_one({'srcDPID': v.get('srcDPID'),
                                          'srcPort': v.get('srcPort'),
                                          'dstDevice': v.get('dstDevice'),
                                          'dstPort': v.get('dstPort')})
                if row is None:
                    ids.append(table.insert(v))
                else:
                    logger.info("(sdn-link) %s already stored!" % (row))
            return ids
        finally:
            self.__mutex.release()
