from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.openflow.manifest_parser import OFv3ManifestParser
from BasePlugin import BasePlugin

import core
logger = core.log.getLogger("sdn-plugin")


class SDNPlugin(BasePlugin):
    def __init__(self):
        super(SDNPlugin, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = OFv3ManifestParser(from_string=m)
            logger.debug("OFv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            slivers = manifest.slivers()
            logger.info("Slivers(%d)=%s" % (len(slivers), slivers,))

            return ({"slivers": slivers}, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e
