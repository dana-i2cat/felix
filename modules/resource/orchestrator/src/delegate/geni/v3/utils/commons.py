from core import dates
from db.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from extensions.sfa.util import xrn
from handler.geni.v3 import exceptions as geni_ex
from rspecs.commons import validate

import core
logger = core.log.getLogger("common-utils")


class CommonUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def fetch_user_name_from_geni_users(geni_users):
        """
        Given the GENI 'geni_users' structure, retrieves the proper
        client or user identifier (may be a name, hrn or urn).
        
        @param geni_users geni_users structure, passed from handler
        @return user identifier
        """
        client_urn = None
        if len(geni_users) >= 1:
            # Any could be used
            #client_urn = geni_users[0]["urn"]
            client_urn = xrn.urn_to_hrn(geni_users[0]["urn"])[0].replace("\\","")
            #client_urn = xrn.get_leaf(xrn.urn_to_hrn(geni_users[0]["urn"])[0])
        return client_urn

    @staticmethod
    def convert_sliver_dates_to_datetime(geni_slivers, geni_expires_value=None):
        """
        Given the GENI slivers structure, converts every 'geni_expires'
        field inside (in rfc3339) format to a datetime object. This is the 
        expected output by CLI clients (e.g. OMNI).
        
        @param geni_slivers slivers structure, generated in delegate
        @param geni_expires_value valid rfc3339 date
        @return geni_slivers slivers structure, with date format modified
        """
        for s in geni_slivers:
            # The 'geni_expires_value' has precedence over the current value
            geni_expires = geni_expires_value or s["geni_expires"]
            if geni_expires is not None:
                s["geni_expires"] = dates.rfc3339_to_datetime(geni_expires)
        logger.debug("RO-Slivers(%d)=%s" % (len(geni_slivers), geni_slivers))
        return geni_slivers

    def validate_rspec(self, rspec):
        """
        Given an RSpec (XML structure), this method validates the
        structure of the document, according to the GENI resource schemas.
        
        @param rspec RSpec defining resources
        @throws GENIv3GeneralError when RSpec format is invalid
        """
        (result, error) = validate(rspec)
        if result is not True:
            m = "RSpec validation failure: %s" % (error,)
            raise geni_ex.GENIv3GeneralError(m)
        logger.info("Validation success!")

    def send_request_allocate_rspec(self, routing_key, req_rspec, slice_urn,
                                    credentials, end_time):
        peer = db_sync_manager.get_configured_peer_by_routing_key(routing_key)
        logger.debug("Peer=%s" % (peer,))
        adaptor, uri = AdaptorFactory.create_from_db(peer)
        logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
        return adaptor.allocate(
            slice_urn, credentials[0]["geni_value"], str(req_rspec), end_time)

    def extend_slivers(self, values, routing_key, slivers, db_slivers):
        logger.info("Slivers=%s" % (values,))
        slivers.extend(values)
        for dbs in values:
            db_slivers.append({"geni_sliver_urn": dbs.get("geni_sliver_urn"),
                               "routing_key": routing_key})

    def manage_renew(self, peer, urns, creds, etime, beffort):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            return adaptor.renew(urns, creds[0]["geni_value"], etime, beffort)
        except Exception as e:
            if beffort:
                logger.error("manage_renew exception: %s", e)
                return []
            else:
                logger.critical("manage_renew exception: %s", e)
                raise e

    def manage_status(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            return adaptor.status(urns, creds[0]["geni_value"])
        except Exception as e:
            logger.error("manage_status exception: %s", e)
            return []

    def manage_operational_action(self, peer, urns, creds, action, beffort):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            return adaptor.perform_operational_action(
                urns, creds[0]["geni_value"], action, beffort)
        except Exception as e:
            # It is possible that some RMs do not implement particular actions
            # e.g. "geni_update_users", etc.
            # http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/
            #  CommonConcepts#SliverOperationalActions
            if beffort:
                if action not in ["geni_start", "geni_stop", "geni_restart"]:
                    raise e
                else:
                    logger.error("manage_operational_action exception: " +
                                 "action=%s, details: %s" % (action, e))
                    return []
            else:
                logger.critical("manage_operational_action exception: " +
                                "action=%s, details: %s" % (action, e))
                raise e

    def manage_delete(self, peer, urns, creds, beffort):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            return adaptor.delete(urns, creds[0]["geni_value"], beffort)
        except Exception as e:
            if beffort:
                logger.error("manage_delete exception: %s" % (e,))
                return []
            else:
                logger.critical("manage_delete exception: %s" % (e,))
                raise e
