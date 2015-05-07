from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.serm.manifest_parser import SERMv3ManifestParser
from rspecs.serm.request_formatter import SERMv3RequestFormatter
from rspecs.commons_tn import Node, Interface
from rspecs.commons_se import SELink
from db.db_manager import db_sync_manager
from commons import CommonUtils

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

    def __update_info_route(self, route, values, key):
        for v in values:
            k, ifs = db_sync_manager.get_se_link_routing_key(v.get(key))
            if k is None:
                logger.warning("%s (%s) is unknown for this SERM!" %
                               (key, v.get(key),))
                continue

        logger.info("Found a match with key=%s, ifs=%s" % (k, ifs,))
        v['routing_key'] = k
        v['internal_ifs'] = ifs
        node = db_sync_manager.get_se_node_info(k)
        v['node'] = node
        if (k is not None) and (k not in route):
            route[k] = SERMv3RequestFormatter()

        # remove all the elements that not have internal_ifs as key!
        values[:] = [v for v in values if 'internal_ifs' in v]

    def __update_nodes(self, nodes, values):
        for v in values:
            if v.get("node") is not None:
                cid = v.get("node").get("component_id")
                cmid = v.get("node").get("component_manager_id")
                if len(nodes) > 0:
                    for i in nodes:
                        if (i.serialize().get("component_id") != cid) and\
                           (i.serialize().get("component_manager_id") != cmid):
                            n = Node(cid, cmid,
                                     sliver_type_name=v.get("routing_key"))
                            nodes.append(n)
                else:
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

    def __create_link(self, if1, if2, sliver_id):
        i = if1.rindex(":")
        n1, name1 = if1[0:i], if1[i+1:len(if1)]
        i = if2.rindex(":")
        n2, name2 = if2[0:i], if2[i+1:len(if1)]

        if n1 != n2:
            raise Exception("SELink: differs node cid (%s,%s)" % (n1, n2))

        cid = n1 + ":" + name1 + "-" + name2
        typee, cm_name = db_sync_manager.get_se_link_info(n1)

        l = SELink(cid, typee, cm_name, sliver=sliver_id)
        l.add_interface_ref(if1)
        l.add_interface_ref(if2)
        return l

    def __update_link(self, links, svalues, tvalues):
        for s in svalues:
            for sintf in s.get("internal_ifs"):
                for t in tvalues:
                    for tintf in t.get("internal_ifs"):
                        if s.get("routing_key") == t.get("routing_key"):
                            l = self.__create_link(sintf.get("component_id"),
                                                   tintf.get("component_id"),
                                                   s.get("routing_key"))
                            links.append(l)

    def __extract_info(self, sdn, tn):
        nodes, links = [], []
        self.__update_nodes(nodes, sdn)
        self.__update_nodes(nodes, tn)
        self.__update_link(links, sdn, tn)

        return [n.serialize() for n in nodes], [l.serialize() for l in links]

    def __update_route_rspec(self, route, sdn_info, tn_info):
        nodes, links = self.__extract_info(sdn_info, tn_info)
        logger.debug("SE-Nodes=%s" % (nodes,))
        logger.debug("SE-Links=%s" % (links,))

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
                raise e

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

    def manage_direct_allocate(self, surn, creds, end, nodes, links):
        route = {}
        self.__update_node_route(route, nodes)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        self.__update_link_route(route, links)
        logger.debug("Links(%d)=%s" % (len(links), links,))

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
                raise e

        return (manifests, slivers, db_slivers)
