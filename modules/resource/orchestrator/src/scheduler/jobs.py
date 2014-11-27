from delegate.geni.v3.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from monitoring_manager import MonitoringManager
from resource_detector import ResourceDetector

import core

logger = core.log.getLogger("jobs")


# resource detector scheduled jobs
def com_resource_detector():
    try:
        rd = ResourceDetector("virtualisation")
        rd.do_action()

    except Exception as e:
        logger.error("com_resource_detector failure: %s" % (e,))


def sdn_resource_detector():
    try:
        rd = ResourceDetector("sdn_networking")
        rd.do_action()

    except Exception as e:
        logger.error("sdn_resource_detector failure: %s" % (e,))


def se_resource_detector():
    try:
        rd = ResourceDetector("stitching_entity")
        rd.do_action()

    except Exception as e:
        logger.error("se_resource_detector failure: %s" % (e,))


def tn_resource_detector():
    try:
        rd = ResourceDetector("transport_network")
        rd.do_action()

    except Exception as e:
        logger.error("sdn_resource_detector failure: %s" % (e,))


# monitoring scheduled jobs
def phy_monitoring():
    try:
        mm = MonitoringManager()
        mm.physical_info()

    except Exception as e:
        logger.error("phy_monitoring failure: %s" % (e,))


# automatic release the slice resources for the end-time expiration
def slice_expiration(urns):
    logger.info("slice expiration timeout: %s" % (urns,))
    ro_slivers = []

    route = db_sync_manager.get_slice_routing_keys(urns)
    logger.debug("Route=%s" % (route,))

    for r, v in route.iteritems():
        peer = db_sync_manager.get_configured_peer(r)
        logger.debug("peer=%s" % (peer,))
        adaptor = AdaptorFactory.create_from_db(peer)
        geni_v3_creds = AdaptorFactory.geni_v3_credentials()
        of_slivers = adaptor.delete(urns, geni_v3_creds, False)

        logger.debug("of_s=%s" % (of_slivers,))
        ro_slivers.extend(of_slivers)

    db_urns = [s.get("geni_sliver_urn") for s in ro_slivers]
    logger.debug("RO-Slivers=%s, DB-URNs=%s" % (ro_slivers, db_urns))
    db_sync_manager.delete_slice_urns(db_urns)
