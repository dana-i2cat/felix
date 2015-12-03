from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser
from rspecs.tnrm.request_formatter import TNRMv3RequestFormatter
from db.db_manager import db_sync_manager
from commons import CommonUtils
from delegate.geni.v3 import exceptions as delegate_ex

from core.config import ConfParser
import ast
import core
logger = core.log.getLogger("tn-utils")


class TNUtils(CommonUtils):
    def __init__(self):
        super(TNUtils, self).__init__()
        w_ = ConfParser("ro.conf").get("tnrm")
        self.__workaround_split_allocation =\
            ast.literal_eval(w_.get("split_workaround"))

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = TNRMv3ManifestParser(from_string=m)
            logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
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

            manifest = TNRMv3ManifestParser(from_string=m)
            logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            return ({"nodes": nodes, "links": links}, urn)
        except Exception as e:
            # It is possible that TNRM does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return ({"nodes": [], "links": []}, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def __update_node_route(self, route, values):
        ret = []
        for v in values:
            # This is a special case of the TNRM module and our deployment in
            # the FELIX testbed in which we have only 1 instance of TNRM and
            # all the islands refer to it. So, the MRO can have the same
            # resources but with different keys (out peers).
            keys = db_sync_manager.get_tn_node_routing_key(
                v.get("component_id"))
            logger.info("Node keys=%s" % (keys,))
            for k in keys:
                tmp = dict(v)
                tmp["routing_key"] = k
                ret.append(tmp)
                if k not in route:
                    route[k] = TNRMv3RequestFormatter()
        return ret

    def __update_link_route(self, route, values):
        ret = []
        for v in values:
            # please refer to the previous comment!
            keys = db_sync_manager.get_tn_link_routing_key(
                v.get("component_id"), v.get("component_manager_name"),
                [i.get("component_id") for i in v.get("interface_ref")])
            logger.info("Link keys=%s" % (keys,))
            for k in keys:
                tmp = dict(v)
                tmp["routing_key"] = k
                ret.append(tmp)
                if k not in route:
                    route[k] = TNRMv3RequestFormatter()
        return ret

    def __update_route_rspec(self, route, nodes, links):
        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("routing_key") == key:
                    rspec.node(n)
            for l in links:
                if l.get("routing_key") == key:
                    rspec.link(l)

    def __extract_se_from_tn(self, nodes, links):
        ret, ifref = [], set()
        for l in links:
            for p in l.get("property"):
                ifref.add(p.get("source_id"))
                ifref.add(p.get("dest_id"))

        for n in nodes:
            for i in n.get("interfaces"):
                if i.get("component_id") in ifref:
                    for v in i.get("vlan"):
                        ret.append({"vlan": v.get("tag"),
                                    "interface": i.get("component_id")})

        return ret

    def __manage_allocate_split_workaround(self, surn, creds, end, ns, ls):
        manifests, slivers, db_slivers, se_tn_info = [], [], [], []
        route = [(n.get("routing_key"), TNRMv3RequestFormatter()) for n in ns]
        for i in xrange(0, len(ns)):
            route[i][1].node(ns[i])
            route[i][1].link(ls[i])

        logger.info("(SPLIT_WORKAROUND)Route: %s" % (route,))
        for r in route:
            try:
                (m, ss) = self.send_request_allocate_rspec(
                    r[0], r[1], surn, creds, end)
                manifest = TNRMv3ManifestParser(from_string=m)
                logger.debug("(SPLIT_WORKAROUND)TNRMv3ManifestParser=%s" %
                             (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("(SPLIT_WORKAROUND)Nodes(%d)=%s" %
                            (len(nodes), nodes,))
                links = manifest.links()
                logger.info("(SPLIT_WORKAROUND)Links(%d)=%s" %
                            (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, r[0], slivers, db_slivers)

                se_tn = self.__extract_se_from_tn(nodes, links)
                logger.debug("(SPLIT_WORKAROUND)SE-TN-INFO=%s" % (se_tn,))
                if len(se_tn) > 0:
                    se_tn_info.extend(se_tn)
            except Exception as e:
                logger.critical("(SPLIT_WORKAROUND)exception: %s", e)
                raise e

        return (manifests, slivers, db_slivers, se_tn_info)

    def manage_allocate(self, surn, creds, end, nodes_in, links_in):
        route = {}
        nodes = self.__update_node_route(route, nodes_in)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        links = self.__update_link_route(route, links_in)
        logger.debug("Links(%d)=%s" % (len(links), links,))

        if self.__workaround_split_allocation:
            # This is a (very)ugly workaround that we MUST remove ASAP!!!
            return self.__manage_allocate_split_workaround(surn, creds, end,
                                                           nodes, links)

        self.__update_route_rspec(route, nodes, links)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers, se_tn_info = [], [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) =\
                    self.send_request_allocate_rspec(k, v, surn, creds, end)
                manifest = TNRMv3ManifestParser(from_string=m)
                logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
                links = manifest.links()
                logger.info("Links(%d)=%s" % (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, k, slivers, db_slivers)

                se_tn = self.__extract_se_from_tn(nodes, links)
                logger.debug("SE-TN-INFO=%s" % (se_tn,))
                if len(se_tn) > 0:
                    se_tn_info.extend(se_tn)
            except Exception as e:
                logger.critical("manage_allocate exception: %s", e)
                raise delegate_ex.AllocationError(
                    str(e), surn, slivers, db_slivers)

        return (manifests, slivers, db_slivers, se_tn_info)

    def find_stps_from_links(self, links_in):
        ret = []
        for link in links_in:
            logger.debug("TNLink=%s" % (link,))
            if len(link.get("property")) > 0:
                # we use only the first item to identify the src/dst stps
                item = link.get("property")[0]
                ret.append({"src_name": item.get("source_id"),
                            "dst_name": item.get("dest_id")})
        return ret

    @staticmethod
    def determine_stp_gre(stp):
        """Determine whether all involved STPs are gre (True) or not (False)"""
        if not isinstance(stp, list):
            stp = [stp]
        return map(lambda x: "gre" in x, stp)
