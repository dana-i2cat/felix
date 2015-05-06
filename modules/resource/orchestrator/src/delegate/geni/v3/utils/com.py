from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.crm.manifest_parser import CRMv3ManifestParser
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
