from db.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.ro.manifest_parser import ROManifestParser
from commons import CommonUtils
from tn import TNUtils
from vl import VLUtils

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
            ret = self.generate_internal_return(m)
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
            ret = self.generate_internal_return(m)
            return (ret, urn)
        except Exception as e:
            # It is possible that RO does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return (ret, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def generate_internal_return(self, m):
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
    def generate_list_resources(rspec, geni_available=False, show_interdomain=False, inner_call=True):
        for n in db_sync_manager.get_com_nodes():
            logger.debug("COM resources node=%s" % (n,))
            rspec.com_node(n, inner_call)

        for d in db_sync_manager.get_sdn_datapaths():
            logger.debug("OF resources dpid=%s" % (d,))
            rspec.datapath(d, inner_call)

        for l in db_sync_manager.get_com_links():
            logger.debug("COM resources link=%s" % (l,))
            rspec.com_link(l, inner_call)

        (of_links, fed_links) = db_sync_manager.get_sdn_links()
        for l in of_links:
            logger.debug("OF resources of-link=%s" % (l,))
            rspec.of_link(l, inner_call)

        for l in fed_links:
            logger.debug("OF resources fed-link=%s" % (l,))
            rspec.fed_link(l, inner_call)

        # Internal use (M/RO) -- OR show inter-domain resources, through config flag
        if inner_call or show_interdomain:
            for n in db_sync_manager.get_tn_nodes():
                logger.debug("TN resources node=%s" % (n,))
                rspec.tn_node(n, inner_call)

            for n in db_sync_manager.get_se_nodes():
                logger.debug("SE resources node=%s" % (n,))
                rspec.se_node(n, inner_call)

            for l in db_sync_manager.get_tn_links():
                logger.debug("TN resources tn-link=%s" % (l,))
                rspec.tn_link(l, inner_call)

            for l in db_sync_manager.get_se_links():
                logger.debug("SE resources se-link=%s" % (l,))
                rspec.se_link(l, inner_call)

        # External use (experimenter) -- OR show inter-domain resources, through config flag
        if geni_available or show_interdomain:
            for l in VLUtils.find_vlinks_from_tn_stps(TNUtils()):
                logger.debug("VL resources vl-link=%s" % (l,))
                rspec.vl_link(l, inner_call)
        return rspec

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
