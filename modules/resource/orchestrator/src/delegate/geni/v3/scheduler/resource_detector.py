from delegate.geni.v3.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
import delegate.geni.v3.rspecs.commons as Commons
from delegate.geni.v3.rspecs.openflow.advertisement_parser\
    import OFv3AdvertisementParser
import core
logger = core.log.getLogger("resource-detector")


class ResourceDetector():
    """
    This object can be used to populate the internal RO's DB
    with the available resources exposed by RMs.
    """
    def __init__(self, typee):
        self.peers = [p for p in db_sync_manager.get_configured_peers()
                      if p.get('type') == typee]

    def do_action(self):
        logger.debug("Configured peers=%d" % (len(self.peers),))
        for peer in self.peers:
            logger.debug("Peer=%s" % (peer,))
            result = self.__get_resources(peer)
            if result is None:
                logger.error("Result is None!")
                continue
            # decode the Adv RSpec now!
            if peer.get('type') == "sdn_networking":
                (dpids, links) = self.__decode_sdn_rspec(result)
                self.__store_sdn_resources(peer.get('_id'), dpids, links)
            elif peer.get('type') == "virtualisation":
                self.__decode_computing_rspec(result)
            else:
                logger.error("Unknown peer type=%s" % (peer.get('type'),))

    def __get_resources(self, peer):
        try:
            adaptor = AdaptorFactory.create_from_db(peer)
            logger.info("RM-Adaptor=%s" % (adaptor,))

            geni_v3_credentials = AdaptorFactory.geni_v3_credentials()
            logger.info("Credentials successfully retrieved!")
            return adaptor.list_resources(geni_v3_credentials, False)

        except Exception as e:
            logger.error("get_resources (%s) exception: %s" % (
                peer.get('type'), str(e),))
            return None

    def __db(self, action, routingKey, data):
        try:
            if action == "store_sdn_datapaths":
                return db_sync_manager.store_sdn_datapaths(routingKey, data)
            elif action == "store_sdn_links":
                return db_sync_manager.store_sdn_links(routingKey, data)
            else:
                logger.error("Unmanaged action type (%s)!" % (action,))

        except Exception as e:
            logger.error("Exception on %s: %s" % (action, str(e)))

    def __decode_sdn_rspec(self, result):
        (ofdpids, links) = (None, None)

        rspec = result.get('value', None)
        if rspec is None:
            logger.error("Unable to get RSpec value from %s" % (result,))
            return (ofdpids, links)

        try:
            of_rspec = OFv3AdvertisementParser(from_string=rspec)
            logger.debug("OFRSpec=%s" % (of_rspec,))
            # validate
            (result, error) = Commons.validate(of_rspec.get_rspec())
            if not result:
                logger.error("Validation failure: %s" % error)
                return (ofdpids, links)

            logger.info("Validation success!")
            ofdpids = of_rspec.datapaths()
            logger.debug("OFDataPaths(%d)=%s" % (len(ofdpids), ofdpids,))

            links = of_rspec.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

        except Exception as e:
            logger.error("Exception: %s" % str(e))
        return (ofdpids, links)

    def __store_sdn_resources(self, peerID, dpids, links):
        if dpids is None or len(dpids) == 0:
            logger.error("Datapaths list does not exist or is empty!")
        else:
            ids = self.__db("store_sdn_datapaths", peerID, dpids)
            logger.info("IDs dpids=%s" % (ids,))

        if links is None or len(links) == 0:
            logger.error("Links list does not exist or is empty!")
        else:
            ids = self.__db("store_sdn_links", peerID, links)
            logger.info("IDs links=%s" % (ids,))

    def __decode_computing_rspec(self, result):
        rspec = result.get('value', None)
        if rspec is None:
            logger.error("Unable to get RSpec value from %s" % (result,))
            return None

        logger.debug("Rspec=%s" % (rspec,))
        return None
