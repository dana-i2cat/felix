from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.ro.manifest_parser import ROManifestParser
from BasePlugin import BasePlugin

import core
logger = core.log.getLogger("ro-plugin")


class ROPlugin(BasePlugin):
    def __init__(self):
        super(ROPlugin, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))

            ret = {"com_nodes": [], "sdn_slivers": [],
                   "tn_nodes": [], "tn_links": [],
                   "se_nodes": [], "se_links": []}
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = ROManifestParser(from_string=m)
            logger.debug("ROManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            ret["com_nodes"] = manifest.com_nodes()
            logger.info("COMNodes(%d)=%s" %
                        (len(ret["com_nodes"]), ret["com_nodes"],))

            ret["sdn_slivers"] = manifest.sdn_slivers()
            logger.info("SDNSlivers(%d)=%s" %
                        (len(ret["sdn_slivers"]), ret["sdn_slivers"],))

            ret["tn_nodes"] = manifest.tn_nodes()
            logger.info("TNNodes(%d)=%s" %
                        (len(ret["tn_nodes"]), ret["tn_nodes"],))

            ret["tn_links"] = manifest.tn_links()
            logger.info("TNLinks(%d)=%s" %
                        (len(ret["tn_links"]), ret["tn_links"],))

            ret["se_nodes"] = manifest.se_nodes()
            logger.info("SENodes(%d)=%s" %
                        (len(ret["se_nodes"]), ret["se_nodes"],))

            ret["se_links"] = manifest.se_links()
            logger.info("SELinks(%d)=%s" %
                        (len(ret["se_links"]), ret["se_links"],))

            return (ret, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e
