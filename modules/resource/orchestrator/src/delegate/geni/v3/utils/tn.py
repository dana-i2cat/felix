from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser
from commons import CommonUtils

import core
logger = core.log.getLogger("tn-utils")


class TNUtils(CommonUtils):
    def __init__(self):
        super(TNUtils, self).__init__()

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