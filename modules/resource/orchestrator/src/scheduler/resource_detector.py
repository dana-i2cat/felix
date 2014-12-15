from db.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory

from rspecs.crm.advertisement_parser import CRMv3AdvertisementParser
from rspecs.openflow.advertisement_parser import OFv3AdvertisementParser
from rspecs.serm.advertisement_parser import SERMv3AdvertisementParser
from rspecs.tnrm.advertisement_parser import TNRMv3AdvertisementParser

import core
import rspecs.commons as Commons

logger = core.log.getLogger("resource-detector")


class ResourceDetector(object):
    """
    This object can be used to populate the internal RO"s DB
    with the available resources exposed by RMs.
    """
    def __init__(self, typee):
        self.peers = [p for p in db_sync_manager.get_configured_peers()
                      if p.get("type") == typee]
        self.typee = typee
        self.adaptor_uri = ""
        self.domain_urn = ""

    def debug(self, msg):
        logger.debug("(%s) %s" % (self.typee, msg))

    def info(self, msg):
        logger.info("(%s) %s" % (self.typee, msg))

    def error(self, msg):
        logger.error("(%s) %s" % (self.typee, msg))

    def do_action(self):
        self.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            self.debug("Peer=%s" % (peer,))
            result, self.adaptor_uri = self.__get_resources(peer)
            if result is None:
                self.error("Result is None!")
                continue
            # Decode the Adv RSpec
            if peer.get("type") == "virtualisation":
                (nodes, links) = self.__decode_com_rspec(result)
                self.__store_com_resources(peer.get("_id"), nodes, links)
            elif peer.get("type") == "sdn_networking":
                (nodes, links) = self.__decode_sdn_rspec(result)
                self.__store_sdn_resources(peer.get("_id"), nodes, links)
            elif peer.get("type") == "stitching_entity":
                (nodes, links) = self.__decode_se_rspec(result)
                self.__store_se_resources(peer.get("_id"), nodes, links)
            elif peer.get("type") == "transport_network":
                (nodes, links) = self.__decode_tn_rspec(result)
                self.__store_tn_resources(peer.get("_id"), nodes, links)
            else:
                self.error("Unknown peer type=%s" % (peer.get("type"),))
            
            # Retrieve sample node, extract domain URN and store
            try:
                self.__set_domain_component_id(nodes[0].get("component_id"))
                db_sync_manager.store_domain_info(self.adaptor_uri, self.domain_urn)
            except Exception as e:
                self.error("Error storing mapping domain_urn:resource_rm. Exception: %s" % e)

    def __get_resources(self, peer):
        try:
            # Retrieve the URI for domain:RMs identification purposes
            adaptor, adaptor_uri = AdaptorFactory.create_from_db(peer)
            self.info("RM-Adaptor=%s" % (adaptor,))

            geni_v3_credentials = AdaptorFactory.geni_v3_credentials()
            self.info("Credentials successfully retrieved!")
            resources_returned = adaptor.list_resources(geni_v3_credentials, False)
            return (resources_returned, adaptor_uri)

        except Exception as e:
            self.error("get_resources (%s) exception: %s" % (
                peer.get("type"), str(e),))
            return None

    def __set_domain_component_id(self, resource_cid):
        """
        Retrieve domain URN from component ID.
        """
        self.domain_urn = resource_cid or self.domain_urn
        #  TODO Process component ID to find URN
        # ...

    def __db(self, action, routingKey, data):
        try:
            try:
                # Methods must be implemented with the EXACT name as the action
                method = getattr(db_sync_manager, action)
            except:
                self.error("Unmanaged action type (%s)!" % (action,))
            # ...And use the same arguments
            return method(routingKey, data)
        except Exception as e:
            self.error("Exception on %s: %s" % (action, str(e)))

    def __decode_com_rspec(self, result):
        (nodes, links) = (None, None)

        rspec = result.get("value", None)
        if not rspec:
            self.error("Unable to get RSpec value from %s" % (result,))
            return (nodes, links)

        try:
            com_rspec = CRMv3AdvertisementParser(from_string=rspec)
            self.debug("COMRSpec=%s" % (com_rspec,))
            # validate
            (result, error) = Commons.validate(com_rspec.get_rspec())
            if not result:
                self.error("Validation failure: %s" % error)
                return (nodes, links)

            self.info("Validation success!")
            nodes = com_rspec.nodes()
            self.info("Nodes(%d)=%s" % (len(nodes), nodes,))

            links = com_rspec.links()
            self.info("Links(%d)=%s" % (len(links), links,))

        except Exception as e:
            self.error("Exception: %s" % str(e))
        return (nodes, links)

    def __decode_sdn_rspec(self, result):
        (ofdpids, links) = (None, None)

        rspec = result.get("value", None)
        if rspec is None:
            self.error("Unable to get RSpec value from %s" % (result,))
            return (ofdpids, links)

        try:
            of_rspec = OFv3AdvertisementParser(from_string=rspec)
            self.debug("OFRSpec=%s" % (of_rspec,))
            # validate
            (result, error) = Commons.validate(of_rspec.get_rspec())
            if not result:
                self.error("Validation failure: %s" % error)
                return (ofdpids, links)

            self.info("Validation success!")
            ofdpids = of_rspec.datapaths()
            self.info("OFDataPaths(%d)=%s" % (len(ofdpids), ofdpids,))

            links = of_rspec.links()
            self.info("Links(%d)=%s" % (len(links), links,))

        except Exception as e:
            self.error("Exception: %s" % str(e))
        return (ofdpids, links)

    def __decode_se_rspec(self, result):
        (nodes, links) = (None, None)

        rspec = result.get("value", None)
        if rspec is None:
            self.error("Unable to get RSpec value from %s" % (result,))
            return (nodes, links)

        try:
            se_rspec = SERMv3AdvertisementParser(from_string=rspec)
            self.debug("SERSpec=%s" % (se_rspec,))
            # validate
            (result, error) = Commons.validate(se_rspec.get_rspec())
            if not result:
                self.error("Validation failure: %s" % error)
                return (nodes, links)

            self.info("Validation success!")
            nodes = se_rspec.nodes()
            self.info("Nodes(%d)=%s" % (len(nodes), nodes,))

            links = se_rspec.links()
            self.info("Links(%d)=%s" % (len(links), links,))

        except Exception as e:
            self.error("Exception: %s" % str(e))
        return (nodes, links)

    def __decode_tn_rspec(self, result):
        (nodes, links) = (None, None)

        rspec = result.get("value", None)
        if rspec is None:
            self.error("Unable to get RSpec value from %s" % (result,))
            return (nodes, links)

        try:
            tn_rspec = TNRMv3AdvertisementParser(from_string=rspec)
            self.debug("TNRSpec=%s" % (tn_rspec,))
            # validate
            (result, error) = Commons.validate(tn_rspec.get_rspec())
            if not result:
                self.error("Validation failure: %s" % error)
                return (nodes, links)

            self.info("Validation success!")
            nodes = tn_rspec.nodes()
            self.info("Nodes(%d)=%s" % (len(nodes), nodes,))

            links = tn_rspec.links()
            self.info("Links(%d)=%s" % (len(links), links,))

        except Exception as e:
            self.error("Exception: %s" % str(e))
        return (nodes, links)

    def __store(self, data, name, action, peer):
        if data is None or len(data) == 0:
            self.error("%s list does not exist or is empty!" % (name,))
        else:
            ids = self.__db(action, peer, data)
            self.info("IDs %s=%s" % (name, ids,))

    def __store_com_resources(self, peerID, dpids, links):
        self.__store(dpids, "Nodes", "store_com_nodes", peerID)
        self.__store(links, "Links", "store_com_links", peerID)

    def __store_sdn_resources(self, peerID, dpids, links):
        self.__store(dpids, "Datapaths", "store_sdn_datapaths", peerID)
        self.__store(links, "Links", "store_sdn_links", peerID)

    def __store_se_resources(self, peerID, nodes, links):
        self.__store(nodes, "Nodes", "store_se_nodes", peerID)
        self.__store(links, "Links", "store_se_links", peerID)

    def __store_tn_resources(self, peerID, nodes, links):
        self.__store(nodes, "Nodes", "store_tn_nodes", peerID)
        self.__store(links, "Links", "store_tn_links", peerID)
