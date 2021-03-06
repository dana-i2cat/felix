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
            return table.find()
        finally:
            self.__mutex.release()

    def get_configured_peer(self, key):
        table = pymongo.MongoClient().felix_ro.RoutingTable
        try:
            self.__mutex.acquire()
            row = table.find_one({"_id": key})
            if row is None:
                raise Exception("RoutingEntry %s not found into RO-DB!" % key)
            return row
        finally:
            self.__mutex.release()

    def update_am_info(self, object_id, am_type, am_version):
        table = pymongo.MongoClient().felix_ro.RoutingTable
        try:
            self.__mutex.acquire()
            table.update({"_id": object_id},
                         {"$set": {"am_type": am_type,
                                   "am_version": am_version}})
        finally:
            self.__mutex.release()

    # (felix_ro) GeneralInfoTable
    def get_domain_id(self):
        table = pymongo.MongoClient().felix_ro.GeneralInfoTable
        try:
            self.__mutex.acquire()
            row = table.find_one()
            if row is None:
                raise Exception("GeneralInfoEntry not found into RO-DB!")
            return row.get("domain")
        finally:
            self.__mutex.release()

    # (felix_ro) SliceTable
    def store_slice_info(self, urn, slivers):
        table = pymongo.MongoClient().felix_ro.SliceTable
        try:
            self.__mutex.acquire()
            row = table.find_one({"slice_urn": urn})
            if row is None:
                entry = {"slice_urn": urn,
                         "slivers": slivers}
                return table.insert(entry)
            # update the slivers list (if needed)
            self.__update_list("slice-table", table, row, "slivers", slivers)
        finally:
            self.__mutex.release()

    def get_slice_routing_keys(self, urns):
        table = pymongo.MongoClient().felix_ro.SliceTable
        try:
            self.__mutex.acquire()
            ret = {}
            for u in urns:
                for r in table.find():
                    for s in r.get("slivers"):
                        if (r.get("slice_urn") == u) or\
                           (s.get("geni_sliver_urn") == u):
                            if (s.get("routing_key") in ret) and\
                               (u not in ret[s.get("routing_key")]):
                                ret[s.get("routing_key")].append(u)
                            else:
                                ret[s.get("routing_key")] = [u]
            return ret
        finally:
            self.__mutex.release()

    def delete_slice_urns(self, urns):
        table = pymongo.MongoClient().felix_ro.SliceTable
        try:
            self.__mutex.acquire()
            rows = table.find()
            for u in urns:
                for r in rows:
                    if r.get("slice_urn") == u:
                        table.remove({"slice_urn": u})
                    else:
                        for s in r.get("slivers"):
                            if s.get("geni_sliver_urn") == u:
                                # remove the element from the list
                                self.__delete_sliver_urn(
                                    table, r.get("slice_urn"),
                                    r.get("slivers"), s)
                                break
        finally:
            self.__mutex.release()

    # (felix_ro) COMNodeTable
    # TODO Ensure correctness
    def store_com_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.COMNodeTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_id": v.get("component_manager_id"), })
                #   "sliver_type_name": v.get("sliver_type_name")})
                if not row:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                self.__update_list("comnodes-table", table, row, "interfaces",
                                   v.get("interfaces"))
            return ids
        finally:
            self.__mutex.release()

    def get_com_nodes(self):
        table = pymongo.MongoClient().felix_ro.COMNodeTable
        try:
            self.__mutex.acquire()
            return table.find()
        finally:
            self.__mutex.release()

    def get_com_node_routing_key(self, cid):
        table = pymongo.MongoClient().felix_ro.COMNodeTable
        try:
            self.__mutex.acquire()
            row = table.find_one({"component_id": cid})
            if row is None:
                raise Exception("CompId %s not found in RO-COMNode-DB!" % cid)
            return row.get("routing_key")
        finally:
            self.__mutex.release()

    # (felix_ro) COMLinkTable
    # TODO Ensure correctness
    def store_com_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.COMLinkTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id")})
                if not row:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                else:
                    logger.debug(
                        "(link-table) %s already stored!" % (row.get("_id")))
            return ids
        finally:
            self.__mutex.release()

    def get_com_links(self):
        table = pymongo.MongoClient().felix_ro.COMLinkTable
        try:
            self.__mutex.acquire()
            return table.find()
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
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_id": v.get("component_manager_id"),
                    "dpid": v.get("dpid")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                self.__update_list("datapth-table", table, row, "ports",
                                   v.get("ports"))
            return ids
        finally:
            self.__mutex.release()

    def get_sdn_datapaths(self):
        table = pymongo.MongoClient().felix_ro.OFDatapathTable
        try:
            self.__mutex.acquire()
            return table.find()
        finally:
            self.__mutex.release()

    def get_sdn_datapath_routing_key(self, dpid):
        table = pymongo.MongoClient().felix_ro.OFDatapathTable
        try:
            self.__mutex.acquire()
            row = table.find_one({
                "component_id": dpid.get("component_id"),
                "component_manager_id": dpid.get("component_manager_id"),
                "dpid": dpid.get("dpid")})
            if row is None:
                raise Exception("Datapath %s not found into RO-DB!" % dpid)
            return row.get("routing_key")
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
                    "routing_key": routingKey,
                    "component_id": v.get("component_id")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                else:
                    logger.debug(
                        "(link-table) %s already stored!" % (row.get("_id")))
            return ids
        finally:
            self.__mutex.release()

    def get_sdn_links(self):
        table = pymongo.MongoClient().felix_ro.OFLinkTable
        (of, fed) = ([], [])
        try:
            self.__mutex.acquire()
            for row in table.find():
                if row.get("dpids") is not None:
                    of.append(row)
                elif row.get("interface_ref_id") is not None:
                    fed.append(row)
            return (of, fed)
        finally:
            self.__mutex.release()

    # (felix_ro) SENodeTable
    def store_se_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.SENodeTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_id": v.get("component_manager_id"),
                    "sliver_type_name": v.get("sliver_type_name")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                self.__update_list("senodes-table", table, row, "interfaces",
                                   v.get("interfaces"))
            return ids
        finally:
            self.__mutex.release()

    def get_se_node_info(self, routingKey):
        table = pymongo.MongoClient().felix_ro.SENodeTable
        try:
            self.__mutex.acquire()
            row = table.find_one({'routing_key': routingKey})
            if row is not None:
                return {
                    'component_id': row.get('component_id'),
                    'component_manager_id': row.get('component_manager_id')}

            return None
        finally:
            self.__mutex.release()

    # (felix_ro) SELinkTable
    def store_se_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.SELinkTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_name": v.get("component_manager_name"),
                    "link_type": v.get("link_type")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                else:
                    logger.debug(
                        "(selink-table) %s already stored!" % (row.get("_id")))
            return ids
        finally:
            self.__mutex.release()

    def get_se_link_routing_key(self, values):
        table = pymongo.MongoClient().felix_ro.SELinkTable
        try:
            key, ifs = None, []
            self.__mutex.acquire()
            for r in table.find():
                ifrefs = r.get('interface_ref')
                for i in ifrefs:
                    if i.get('component_id') in values:
                        key = r.get('routing_key')
                        ifrefs.remove(i)
                        ifs.append(ifrefs[0])
            return key, ifs
        finally:
            self.__mutex.release()

    def get_se_link_info(self, node_cid):
        table = pymongo.MongoClient().felix_ro.SELinkTable
        try:
            self.__mutex.acquire()
            for r in table.find():
                i = r.get('component_id').find(node_cid)
                if i != -1:
                    return r.get('link_type'), r.get('component_manager_name')

            return None, None
        finally:
            self.__mutex.release()

    # (felix_ro) TNNodeTable
    def store_tn_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.TNNodeTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_id": v.get("component_manager_id"),
                    "sliver_type_name": v.get("sliver_type_name")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                    continue
                # update the object (if needed)
                self.__update_list("tnnodes-table", table, row, "interfaces",
                                   v.get("interfaces"))
            return ids
        finally:
            self.__mutex.release()

    def get_tn_nodes(self):
        table = pymongo.MongoClient().felix_ro.TNNodeTable
        try:
            self.__mutex.acquire()
            return table.find()
        finally:
            self.__mutex.release()

    def get_tn_node_routing_key(self, cid):
        table = pymongo.MongoClient().felix_ro.TNNodeTable
        try:
            self.__mutex.acquire()
            row = table.find_one({"component_id": cid})
            if row is None:
                raise Exception("CompId %s not found into RO-TNNode-DB!" % cid)
            return row.get("routing_key")
        finally:
            self.__mutex.release()

    # (felix_ro) TNLinkTable
    def store_tn_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.TNLinkTable
        try:
            ids = []
            self.__mutex.acquire()
            for v in values:
                row = table.find_one({
                    "routing_key": routingKey,
                    "component_id": v.get("component_id"),
                    "component_manager_name": v.get("component_manager_name")})
                if row is None:
                    v["routing_key"] = routingKey
                    ids.append(table.insert(v))
                else:
                    logger.debug(
                        "(tnlink-table) %s already stored!" % (row.get("_id")))
            return ids
        finally:
            self.__mutex.release()

    def get_tn_links(self):
        table = pymongo.MongoClient().felix_ro.TNLinkTable
        try:
            self.__mutex.acquire()
            return table.find()
        finally:
            self.__mutex.release()

    def get_tn_link_routing_key(self, cid, cmid, ifrefs):
        try:
            self.__mutex.acquire()
            table = pymongo.MongoClient().felix_ro.TNLinkTable
            row = table.find_one({"component_id": cid})
            if row is not None:
                return row.get("routing_key")

            table = pymongo.MongoClient().felix_ro.TNNodeTable
            row = table.find_one({"component_manager_id": cmid})
            if row is not None:
                return row.get("routing_key")

            for row in table.find():
                for i in row.get("interfaces"):
                    if i.get("component_id") in ifrefs:
                        return row.get("routing_key")

            raise Exception("Link (%s,%s,%s) owner is not found into RO-DB!" %
                            (cid, cmid, ifrefs))
        finally:
            self.__mutex.release()

    # utilities
    def __update_list(self, tname, table, entry, key, values):
        logger.debug("(%s) %s already stored!" % (tname, entry.get("_id"),))
        modif = {key: []}
        for v in values:
            if v not in entry.get(key):
                modif.get(key).append(v)

        if len(modif.get(key)) > 0:
            modif.get(key).extend(entry.get(key))
            logger.debug("(%s) extend slivers info %s" % (tname, modif,))
            table.update({"_id": entry.get("_id")},
                         {"$set": modif})
        else:
            logger.debug("(%s) not needed to update %s" % (tname, key,))

    def __delete_sliver_urn(self, table, slice_urn, slivers, elem):
        logger.debug("(slice-table) %s remove %s from %s" %
                     (slice_urn, elem, slivers))
        slivers.remove(elem)
        modif = {"slivers": slivers}
        table.update({"slice_urn": slice_urn},
                     {"$set": modif})

# This is the db manager object to be used into other modules
db_sync_manager = DBManager()
