from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.crm.manifest_parser import CRMv3ManifestParser
from rspecs.crm.request_formatter import CRMv3RequestFormatter
from db.db_manager import db_sync_manager
from commons import CommonUtils

import core
logger = core.log.getLogger("com-utils")


class COMUtils(CommonUtils):
    def __init__(self):
        super(COMUtils, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = CRMv3ManifestParser(from_string=m)
            logger.debug("CRMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))

            return ({"nodes": nodes}, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e

    def manage_provision(self, peer, urns, creds, beffort, etime, gusers):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn = adaptor.provision(
                urns, creds[0]["geni_value"], beffort, etime, gusers)

            manifest = CRMv3ManifestParser(from_string=m)
            logger.debug("CRMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))

            return ({"nodes": nodes}, urn)
        except Exception as e:
            # It is possible that CRM does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return ({"nodes": []}, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def __update_route(self, route, values):
        for v in values:
            cid = v.get("component_id")
            k = db_sync_manager.get_com_node_routing_key(cid)
            v["routing_key"] = k
            if k not in route:
                route[k] = CRMv3RequestFormatter()

    def __update_route_rspec(self, route, slivers):
        for key, rspec in route.iteritems():
            for s in slivers:
                if s.get("routing_key") == key:
                    rspec.node(s)

    def manage_allocate(self, slice_urn, credentials, slice_expiration,
                        slivers, parser):
        route = {}
        self.__update_route(route, slivers)
        logger.debug("Slivers=%s" % (slivers,))

        self.__update_route_rspec(route, slivers)
        logger.info("Route=%s" % (route,))
        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) = self.send_request_allocate_rspec(
                    k, v, slice_urn, credentials, slice_expiration)
                manifest = CRMv3ManifestParser(from_string=m)
                logger.debug("CRMv3ManifestParser=%s" % (manifest,))

                nodes = manifest.nodes()
                logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
                manifests.append({"nodes": nodes})

                self.extend_slivers(ss, k, slivers, db_slivers)
            except Exception as e:
                logger.critical("manage_allocate exception: %s", e)
                raise e

        return (manifests, slivers, db_slivers)
