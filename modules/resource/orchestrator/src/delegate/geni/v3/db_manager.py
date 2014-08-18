import pymongo
import threading

import core
logger = core.log.getLogger("db-manager")


class DBManager(object):
    """This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db"""
    def __init__(self):
        self.__mutex = threading.Lock()

    # (felix_ro) RoutingTable
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

    # (felix_ro) OFDatapathTable
    def store_sdn_datapaths(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.OFDatapathTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    'routing_key': routingKey,
                    'component_id': v.get('component_id'),
                    'component_manager_id': v.get('component_manager_id'),
                    'dpid': v.get('dpid')})
                if row is None:
                    v['routing_key'] = routingKey
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                logger.debug(
                    "(datapth-table) %s already stored!" % (row.get('_id')))
                modif = {'ports': []}
                for p in v.get('ports'):
                    if p not in row.get('ports'):
                        modif.get('ports').append(p)

                if len(modif.get('ports')) > 0:
                    modif.extend(row.get('ports'))
                    logger.debug(
                        "(datapth-table) extend port info %s" % (modif))
                    table.update({'_id': row.get('_id')},
                                 {"$set": modif})
            return ids
        finally:
            self.__mutex.release()

    # (felix_ro) OFLinkTable
    def store_sdn_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.OFLinkTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    'routing_key': routingKey,
                    'component_id': v.get('component_id')})
                if row is None:
                    v['routing_key'] = routingKey
                    ids.append(table.insert(v))
                else:
                    logger.debug(
                        "(link-table) %s already stored!" % (row.get('_id')))
            return ids
        finally:
            self.__mutex.release()
