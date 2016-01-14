import core
from resource_detector import ResourceDetector
from db.db_manager import db_sync_manager

logger = core.log.getLogger("resource-updater")


class ResourceUpdater(ResourceDetector):
    def __init__(self, typee):
        super(ResourceUpdater, self).__init__(typee)

    def debug(self, msg):
        logger.debug("(%s) %s" % (self.typee, msg))

    def info(self, msg):
        logger.info("(%s) %s" % (self.typee, msg))

    def error(self, msg):
        logger.error("(%s) %s" % (self.typee, msg))

    def do_tn_action(self):
        self.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            self.debug("Peer=%s" % (peer,))
            result, self.adaptor_uri = self.get_resources(peer, True)
            if result is None:
                self.error("Peer is not returning resources via ListRes!")
                continue
            # Decode the Adv RSpec per RM (RO level)
            if peer.get("type") == self.allowed_peers.get("PEER_TNRM"):
                (nodes, links) = self.decode_tn_rspec(result)
                # There aren't any links in the TNRM adv-rspec,
                # so there is not need to manage them!
                self.__update_tn_nodes(peer.get("_id"), nodes)
            else:
                self.error("Unknown/Unmanaged peer type=%s" %
                           (peer.get("type"),))

    def __update_tn_nodes(self, peerid, nodes):
        if nodes and len(nodes) > 0:
            ids = db_sync_manager.update_tn_nodes(peerid, nodes)
            logger.debug("TN-nodes ids: %s" % (ids))
