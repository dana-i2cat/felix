from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.serm.manifest_parser import SERMv3ManifestParser
from rspecs.serm.request_formatter import SERMv3RequestFormatter
from rspecs.commons_tn import Node, Interface
from rspecs.commons_se import SELink
from db.db_manager import db_sync_manager
from commons import CommonUtils
from delegate.geni.v3 import exceptions as delegate_ex

import core
logger = core.log.getLogger("se-utils")


class SEUtils(CommonUtils):
    def __init__(self):
        super(SEUtils, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = SERMv3ManifestParser(from_string=m)
            logger.debug("SERMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            return ({"nodes": nodes, "links": links}, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e

    def manage_provision(self, peer, urns, creds, beffort, etime, gusers):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn = adaptor.provision(
                urns, creds[0]["geni_value"], beffort, etime, gusers)

            manifest = SERMv3ManifestParser(from_string=m)
            logger.debug("SERMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            return ({"nodes": nodes, "links": links}, urn)
        except Exception as e:
            # It is possible that SERM does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return ({"nodes": [], "links": []}, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def __extract_nodeid_from_ifs(self, interfaces):
        # we are assuming here to extract the first node identifier
        # (only 1 SE node for each island)
        for i in interfaces:
            index = i.get('component_id').rindex("_")
            return i.get('component_id')[0:index]

        return None

    def __update_info_route(self, route, values, key):
        for v in values:
            logger.debug("Key=%s, Value=%s" % (key, v))
            k, ifs = db_sync_manager.get_se_link_routing_key(v.get(key))
            if k is None:
                logger.warning("The key (%s) for (%s) is unknown for " %
                               (key, v.get(key),) + "this SERM!")
                continue

            logger.info("Found a match with key=%s, ifs=%s" % (k, ifs,))
            v['routing_key'] = k
            v['internal_ifs'] = ifs
            # we need to extract the node-id from the interface identifier
            node_id = self.__extract_nodeid_from_ifs(ifs)
            node = db_sync_manager.get_se_node_info(k, node_id)
            logger.info("Reference Node=%s" % (node))
            v['node'] = node
            if (k is not None) and (k not in route):
                route[k] = SERMv3RequestFormatter()

        # remove all the elements that not have internal_ifs as key!
        values[:] = [v for v in values if 'internal_ifs' in v]

    def __is_node_present(self, nodes, cid, cmid):
        for n in nodes:
            if (n.serialize().get("component_id") == cid) and\
               (n.serialize().get("component_manager_id") == cmid):
                return True
        return False

    def __update_nodes(self, nodes, values):
        for v in values:
            if v.get("node") is not None:
                cid = v.get("node").get("component_id")
                cmid = v.get("node").get("component_manager_id")
                if not self.__is_node_present(nodes, cid, cmid):
                    n = Node(cid, cmid, sliver_type_name=v.get("routing_key"))
                    nodes.append(n)

        for v in values:
            if v.get("node") is not None:
                for n in nodes:
                    scid = v.get("node").get("component_id")
                    scmid = v.get("node").get("component_manager_id")
                    ncid = n.serialize().get("component_id")
                    ncmid = n.serialize().get("component_manager_id")
                    if (scid == ncid) and (scmid == ncmid):
                        for i in v.get("internal_ifs"):
                            intf = Interface(i.get("component_id"))
                            intf.add_vlan(v.get("vlan"), "")
                            n.add_interface(intf.serialize())

    def __create_link(self, if1, if2, vlan1, vlan2, sliver_id):
        """
        Generates the SE link in a proper format:
            <urn_dpid_1>_<port1>_<dpid2>_<port2>_<vlan1>_<vlan2>
        """
        i = if1.rindex("_")
        n1, num1 = if1[0:i], if1[i+1:len(if1)]
        i = if2.rindex("_")
        n2, num2 = if2[0:i], if2[i+1:len(if2)]
        dpid2 = n2[n2.rindex("+")+1:]

        cid = n1 + "_" + num1 + "_" + dpid2 + "_" + num2
        logger.debug("cid=%s, node-id=%s, port-num1=%s, port-num2=%s" %
                     (cid, n1, num1, num2,))
        typee, cm_name = db_sync_manager.get_se_link_info(n1 + "_" + num1)

        l = SELink(cid, typee, cm_name, sliver=sliver_id)
        l.add_interface_ref(if1, vlan1)
        l.add_interface_ref(if2, vlan2)
        return l

    def __check_for_consistency(self, sdn_routing_key, tn_routing_key,
                                sdn_if_id, tn_if_id):
        if sdn_routing_key != tn_routing_key:
            logger.info("Different routing keys (%s),(%s)" %
                        (sdn_routing_key, tn_routing_key))
            return False

        i = sdn_if_id.rindex("_")
        nodeid1 = sdn_if_id[0:i]
        i = tn_if_id.rindex("_")
        nodeid2 = tn_if_id[0:i]

        # In case of MRO-MRO communication the two node ids can be differs!
        if nodeid1 != nodeid2:
            logger.info("Different node ids (%s),(%s)" % (nodeid1, nodeid2))
            return False

        return True

    def __update_link(self, links, svalues, tvalues):
#        added_links = []
        for s in svalues:
            for sintf in s.get("internal_ifs"):
                for t in tvalues:
                    for tintf in t.get("internal_ifs"):
                        ret = self.__check_for_consistency(
                            s.get("routing_key"), t.get("routing_key"),
                            sintf.get("component_id"),
                            tintf.get("component_id"))
                        if ret:
                            l = self.__create_link(sintf.get("component_id"),
                                                   tintf.get("component_id"),
                                                   s.get("vlan"),
                                                   t.get("vlan"),
                                                   s.get("routing_key"))
#                            l_add = {"sdn_cid": sintf.get("component_id"),
#                                    "tn_cid": tintf.get("component_id")}
#                            if l_add not in added_links:
#                                links.append(l)
#                                added_links.append(l_add)
                            links.append(l)

    def __extract_info(self, sdn, tn):
        nodes, links = [], []
        self.__update_nodes(nodes, sdn)
        self.__update_nodes(nodes, tn)
        self.__update_link(links, sdn, tn)

        return [n.serialize() for n in nodes], [l.serialize() for l in links]

    def __update_route_rspec(self, route, sdn_info, tn_info):
        nodes, links = self.__extract_info(sdn_info, tn_info)
        logger.debug("SE-Nodes(%d)=%s" % (len(nodes), nodes,))
        logger.debug("SE-Links(%d)=%s" % (len(links), links,))

        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("sliver_type_name") == key:
                    n["sliver_type_name"] = None
                    rspec.node(n)

            for l in links:
                if l.get("sliver_id") == key:
                    l["sliver"] = None
                    rspec.link(l)

    def manage_allocate(self, surn, creds, end, sdn_info, tn_info):
        route = {}
        self.__update_info_route(route, sdn_info, "dpids")
        logger.debug("SE-SdnInfo(%d)=%s" % (len(sdn_info), sdn_info,))
        self.__update_info_route(route, tn_info, "interface")
        logger.debug("SE-TnInfo(%d)=%s" % (len(tn_info), tn_info,))

        self.__update_route_rspec(route, sdn_info, tn_info)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) =\
                    self.send_request_allocate_rspec(k, v, surn, creds, end)
                manifest = SERMv3ManifestParser(from_string=m)
                logger.debug("SERMv3ManifestParser=%s" % (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
                links = manifest.links()
                logger.info("Links(%d)=%s" % (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, k, slivers, db_slivers)
            except Exception as e:
                logger.critical("manage_allocate exception: %s", e)
                raise delegate_ex.AllocationError(
                    str(e), surn, slivers, db_slivers)

        return (manifests, slivers, db_slivers)

    def __update_node_route(self, route, values):
        for v in values:
            k = db_sync_manager.get_se_node_routing_key(v.get("component_id"))
            v["routing_key"] = k
            if k not in route:
                route[k] = SERMv3RequestFormatter()

    def __update_link_route(self, route, values):
        for v in values:
            k = db_sync_manager.get_direct_se_link_routing_key(
                v.get("component_id"),
                [i.get("component_id") for i in v.get("interface_ref")])
            v["routing_key"] = k
            if k not in route:
                route[k] = SERMv3RequestFormatter()

    def __update_direct_route_rspec(self, route, nodes, links):
        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("routing_key") == key:
                    rspec.node(n)
            for l in links:
                if l.get("routing_key") == key:
                    rspec.link(l)

    def __update_link_with_vlantag(self, nodes, links):
        ret = {}
        for n in nodes:
            for i in n.get('interfaces'):
                for v in i.get('vlan'):
                    ret[i.get('component_id')] = v.get('tag')

        for l in links:
            for i in l.get('interface_ref'):
                i['vlantag'] = ret.get(i.get('component_id'))

    def manage_direct_allocate(self, surn, creds, end, nodes, links):
        route = {}
        self.__update_node_route(route, nodes)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        self.__update_link_route(route, links)
        logger.debug("Links(%d)=%s" % (len(links), links,))

        # XXX_FIXME_XXX: the SERM requires a new field in the link attribute
        # (felix:vlan). This is not compatible with the GENI world...
        self.__update_link_with_vlantag(nodes, links)
        logger.warning("Updated Links(%d)=%s" % (len(links), links,))

        self.__update_direct_route_rspec(route, nodes, links)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) =\
                    self.send_request_allocate_rspec(k, v, surn, creds, end)
                manifest = SERMv3ManifestParser(from_string=m)
                logger.debug("SERMv3ManifestParser=%s" % (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
                links = manifest.links()
                logger.info("Links(%d)=%s" % (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, k, slivers, db_slivers)
            except Exception as e:
                logger.critical("manage_direct_allocate exception: %s", e)
                raise delegate_ex.AllocationError(
                    str(e), surn, slivers, db_slivers)

        return (manifests, slivers, db_slivers)
