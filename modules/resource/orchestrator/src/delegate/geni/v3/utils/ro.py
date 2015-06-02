from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.ro.manifest_parser import ROManifestParser
from commons import CommonUtils

import core
logger = core.log.getLogger("ro-utils")


class ROUtils(CommonUtils):
    def __init__(self):
        super(ROUtils, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])
            ret = ROUtils.generate_internal_r1eturn(m)
            return (ret, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e

    def manage_provision(self, peer, urns, creds, beffort, etime, gusers):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn = adaptor.provision(
                urns, creds[0]["geni_value"], beffort, etime, gusers)
            ret = ROUtils.generate_internal_return(m)
            return (ret, urn)
        except Exception as e:
            # It is possible that RO does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return (ret, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    @staticmethod
    def generate_internal_return(m):
        ret = {"com_nodes": [], "sdn_slivers": [],
            "tn_nodes": [], "tn_links": [],
            "se_nodes": [], "se_links": []}

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
        return ret

    @staticmethod
    def generate_describe_manifest(ro_manifest, ro_m_info):
        for n in ro_m_info.get("com_nodes"):
            ro_manifest.com_node(n)
        for s in ro_m_info.get("sdn_slivers"):
            ro_manifest.of_sliver(s)
        for n in ro_m_info.get("tn_nodes"):
            ro_manifest.tn_node(n)
        for l in ro_m_info.get("tn_links"):
            ro_manifest.tn_link(l)
        for n in ro_m_info.get("se_nodes"):
            ro_manifest.se_node(n)
        for l in ro_m_info.get("se_links"):
            ro_manifest.se_link(l)
        return ro_manifest
