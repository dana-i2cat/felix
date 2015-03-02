import core
import pymongo
import re
import threading
import urlparse

logger = core.log.getLogger("db-manager")

##
# Quick reference of existing collections under "felix_ro" database
#
#   domain.routing
#   resource.com.node
#   resource.com.link
#   resource.of.node
#   resource.of.link
#   resource.se.node
#   resource.se.link
#   resource.tn.node
#   resource.tn.link
#   topology.physical
#   topology.slice
#


class DBManager(object):
    """
    This object is a wrapper for MongoClient to communicate to the RO
    (local) mongo-db
    """

    def __init__(self):
        self.__mutex = threading.Lock()

    def __check_return_rows(self, rows, custom_table, filter_params={}):
        if rows is None:
            raise Exception("%s -- could not find entry with params=%s!" %
                            (custom_table.full_name, filter_params))
        return rows

    def __get_one(self, custom_table, filter_params={}):
        table = custom_table
        try:
            self.__mutex.acquire()
            row = table.find_one(filter_params)
            return self.__check_return_rows(row, custom_table, filter_params)
        finally:
            self.__mutex.release()

    def __get_all(self, custom_table, filter_params={}):
        table = custom_table
        try:
            self.__mutex.acquire()
            rows = table.find(filter_params)
            return self.__check_return_rows(rows, custom_table, filter_params)
        finally:
            self.__mutex.release()

    def __set_update(self, custom_table, object_id, fields_dict={}):
        table = custom_table
        try:
            self.__mutex.acquire()
            table.update({"_id": object_id},
                         {"$set": fields_dict})
        finally:
            self.__mutex.release()

    # (felix_ro) domain.routing
    def get_configured_peers(self):
        """
        Collection that stores peers (either RMs or ROs)
        """
        table = pymongo.MongoClient().felix_ro.domain.routing
        return self.__get_all(table)

    def get_configured_peer(self, filter_params):
        table = pymongo.MongoClient().felix_ro.domain.routing
        return self.__get_one(table, filter_params)

    def get_configured_peer_by_routing_key(self, key):
        filter_params = {"_id": key}
        return self.get_configured_peer(filter_params)

    def get_configured_peer_by_uri(self, rm_url):
        # Parse URL in order to filtering entry in domain.routing collection
        rm_url = urlparse.urlparse(rm_url)
        rm_endpoint = rm_url.path
        # Remove internal slashes
        if rm_endpoint[0] == "/":
            rm_endpoint = rm_endpoint[1:]
        if rm_endpoint[-1] == "/":
            rm_endpoint = rm_endpoint[:-1]
        rm_address, rm_port = rm_url.netloc.split(":")
        rm_protocol = rm_url.scheme
        rm_endpoint_re = self.__get_regexp_for_query(rm_endpoint)
        # Prepare "rm_endpoint" for "like" query (as regexp)
        # rm_endpoint = rm_endpoint.replace("/","\/")
        filter_params = {"protocol": rm_protocol, "address": rm_address,
                         "port": rm_port, "endpoint": rm_endpoint_re, }
        peer = self.get_configured_peer(filter_params)
        return peer

    # TODO Consider making this more flexible by passing
    # a dictionary with any parameter
    def update_peer_info(self, object_id, am_type, am_version):
        table = pymongo.MongoClient().felix_ro.domain.routing
        fields_dict = {"am_type": am_type,
                       "am_version": am_version}
        self.__set_update(table, object_id, fields_dict)

    def set_peer_urn(self, object_id, domain_urn):
        table = pymongo.MongoClient().felix_ro.domain.routing
        fields_dict = {"domain_urn": domain_urn}
        self.__set_update(table, object_id, fields_dict)

    # (felix_ro) domain.info
    def store_domain_info(self, rm_url, domain_urn):
        table = pymongo.MongoClient().felix_ro.domain.info
        # Search for entry in domain.routing first
        peer = self.get_configured_peer_by_uri(rm_url)
        # Search in domain.routing for any RM matching the filtering parameters
        try:
            self.__mutex.acquire()
            row = table.find_one({"_ref_peer": peer.get("_id")})
            if not row:
                entry = {"domain_urn": domain_urn,
                         "_ref_peer": peer.get("_id")}
                return table.insert(entry)
        except:
            pass
        finally:
            self.__mutex.release()

    def get_domain_info(self, filter_params):
        table = pymongo.MongoClient().felix_ro.domain.info
        return self.__get_one(table, filter_params)

    def get_domain_urn(self, filter_params):
        return self.get_domain_info(filter_params).get("domain_urn")

    # (felix_ro) topology.physical
    def store_physical_info(self, domain_urn, last_update):
        """
        Keep track of last update time for physical topology within a domain.
        """
        table = pymongo.MongoClient().felix_ro.topology.physical
        # Get ID of domain related to physical topology
        domain = self.get_domain_info({"domain_urn": domain_urn})
        try:
            self.__mutex.acquire()
            row = table.find_one({"_ref_domain": domain.get("_id")})
            if row is None:
                entry = {"last_update": last_update,
                         "_ref_domain": domain.get("_id"), }
                return table.insert(entry)
        except:
            pass
        finally:
            self.__mutex.release()

    def get_physical_info_from_domain(self, domain_id):
        """
        Retrieve physical topology information through domain.info's ID.
        """
        table = pymongo.MongoClient().felix_ro.topology.physical
        filter_params = {"_ref_domain": domain_id}
        return self.__get_one(table, filter_params)

    # (felix_ro) topology.slice
    def store_slice_info(self, urn, slivers):
        table = pymongo.MongoClient().felix_ro.topology.slice
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
        table = pymongo.MongoClient().felix_ro.topology.slice
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
        table = pymongo.MongoClient().felix_ro.topology.slice
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

    # (felix_ro) resource.com.node
    # TODO Ensure correctness
    def store_com_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.com.node
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

    def get_com_nodes(self, filter_params={}):
        table = pymongo.MongoClient().felix_ro.resource.com.node
        return self.__get_all(table, filter_params)

    def get_com_nodes_by_domain(self, domain_urn):
        # Domain URN = Domain authority
        # Remove the bit of the authority,
        # then create a RE that starts this way
        domain_urn = domain_urn.split("+authority+")[0]
        domain_urn_re = self.__get_regexp_for_query(domain_urn)

        # Look for all those resources that start with a given URN
        filter_params = {"component_id": domain_urn_re, }
        nodes = self.get_com_nodes(filter_params)
        return nodes

    def get_com_node_routing_key(self, cid):
        table = pymongo.MongoClient().felix_ro.resource.com.node
        filter_params = {"component_id": cid}
        return self.__get_one(table, filter_params).get("routing_key")

    # (felix_ro) resource.com.link
    # TODO Ensure correctness
    def store_com_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.com.link
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

    def get_com_links(self, filter_params={}):
        table = pymongo.MongoClient().felix_ro.resource.com.link
        return self.__get_all(table, filter_params)

    def get_com_links_by_domain(self, domain_urn):
        # Domain URN = Domain authority
        # Remove the bit of the authority,
        # then create a RE that starts this way
        domain_urn = domain_urn.split("+authority+")[0]
        domain_urn_re = self.__get_regexp_for_query(domain_urn)

        # Look for all those resources that start with a given URN
        filter_params = {"component_id": domain_urn_re, }
        links = self.get_com_links(filter_params)
        return links

    # (felix_ro) resource.of.node
    def store_sdn_datapaths(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.of.node
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

    def get_sdn_datapaths(self, filter_params={}):
        table = pymongo.MongoClient().felix_ro.resource.of.node
        return self.__get_all(table, filter_params)

    def get_sdn_datapaths_by_domain(self, domain_urn):
        # Domain URN = Domain authority
        # Remove the bit of the authority,
        # then create a RE that starts this way
        domain_urn = domain_urn.split("+authority+")[0]
        domain_urn_re = self.__get_regexp_for_query(domain_urn)

        # Look for all those resources that start with a given URN
        filter_params = {"component_id": domain_urn_re, }
        nodes = self.get_sdn_datapaths(filter_params)
        return nodes

    def get_sdn_datapath_routing_key(self, dpid):
        table = pymongo.MongoClient().felix_ro.resource.of.node
        filter_params =\
            {"component_id": dpid.get("component_id"),
             "component_manager_id": dpid.get("component_manager_id"),
             "dpid": dpid.get("dpid")}
        return self.__get_one(table, filter_params).get("routing_key")

    # (felix_ro) resource.of.link
    def store_sdn_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.of.link
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

    def get_sdn_links(self, filter_params={}):
        table = pymongo.MongoClient().felix_ro.resource.of.link
        (of, fed) = ([], [])
        try:
            self.__mutex.acquire()
            for row in table.find(filter_params):
                if row.get("dpids") is not None:
                    of.append(row)
                elif row.get("interface_ref_id") is not None:
                    fed.append(row)
            return (of, fed)
        finally:
            self.__mutex.release()

    def get_sdn_links_by_domain(self, domain_urn):
        # Domain URN = Domain authority
        # Remove the bit of the authority,
        # then create a RE that starts this way
        domain_urn = domain_urn.split("+authority+")[0]
        domain_urn_re = self.__get_regexp_for_query(domain_urn)

        # Look for all those resources that start with a given URN
        filter_params = {"component_id": domain_urn_re, }
        links = self.get_sdn_links(filter_params)
        return links

    # (felix_ro) resource.se.node
    def store_se_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.se.node
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
        table = pymongo.MongoClient().felix_ro.resource.se.node
        filter_params = {'routing_key': routingKey}
        row = self.__get_one(table, filter_params)
        # Row has some value if passed this point
        return {'component_id': row.get('component_id'),
                'component_manager_id': row.get('component_manager_id')}

    def get_se_nodes(self):
        table = pymongo.MongoClient().felix_ro.resource.se.node
        return self.__get_all(table)

    # (felix_ro) resource.se.link
    def store_se_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.se.link
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
        table = pymongo.MongoClient().felix_ro.resource.se.link
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
        table = pymongo.MongoClient().felix_ro.resource.se.link
        try:
            self.__mutex.acquire()
            for r in table.find():
                i = r.get('component_id').find(node_cid)
                if i != -1:
                    return r.get('link_type'), r.get('component_manager_name')

            return None, None
        finally:
            self.__mutex.release()

    def get_se_links(self):
        table = pymongo.MongoClient().felix_ro.resource.se.link
        return self.__get_all(table)

    # (felix_ro) resource.tn.node
    def store_tn_nodes(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.tn.node
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
        table = pymongo.MongoClient().felix_ro.resource.tn.node
        return self.__get_all(table)

    def get_tn_node_routing_key(self, cid):
        table = pymongo.MongoClient().felix_ro.resource.tn.node
        filter_params = {"component_id": cid}
        return self.__get_one(table, filter_params).get("routing_key")

    # (felix_ro) resource.tn.link
    def store_tn_links(self, routingKey, values):
        table = pymongo.MongoClient().felix_ro.resource.tn.link
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
        table = pymongo.MongoClient().felix_ro.resource.tn.link
        return self.__get_all(table)

    def get_tn_link_routing_key(self, cid, cmid, ifrefs):
        try:
            self.__mutex.acquire()
            table = pymongo.MongoClient().felix_ro.resource.tn.link
            row = table.find_one({"component_id": cid})
            if row is not None:
                return row.get("routing_key")

            table = pymongo.MongoClient().felix_ro.resource.tn.node
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

    def __get_regexp_for_query(self, search_term):
        terms_to_replace = ["+"]
        for term in terms_to_replace:
            search_term = search_term.replace(term, "\%s" % term)
        return re.compile(search_term)


# This is the db manager object to be used into other modules
db_sync_manager = DBManager()
