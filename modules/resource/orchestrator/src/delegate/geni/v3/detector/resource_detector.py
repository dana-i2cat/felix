from delegate.geni.v3.db_manager import DBManager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from core.config import ConfParser
from core.service import Service
import ast


class ResourceDetector(Service):
    """
    This object can be used to populate the internal RO's DB
    with the available resources exposed by RMs.
    """

    def __init__(self, interval=30):
        self.config = ConfParser("ro.conf")
        self.interval = ast.literal_eval(
            self.config.get("service \"resource_detector\"").get("interval"))
        super(ResourceDetector, self).__init__(
            "ResourceDetector", self.interval)

    def do_action(self):
        peers = DBManager().get_configured_peers()
        self.debug("Configured peers=%d" % (len(peers),))
        for peer in peers:
            self.debug("Peer=%s" % (peer,))
            if peer.get('type') == "sdn_networking":
                self.__do_sdn_action(peer)
            elif peer.get('type') == "virtualisation":
                self.__do_computing_action(peer)
            else:
                self.error("Unknown peer type=%s" % (peer.get('type'),))

    def __do_sdn_action(self, peer):
        try:
            adaptor = AdaptorFactory.create(
                type=peer.get('type'),
                protocol=peer.get('protocol'),
                user=peer.get('user'),
                password=peer.get('password'),
                address=peer.get('address'),
                port=peer.get('port'),
                endpoint=peer.get('endpoint'),
                id=peer.get('_id'),
                am_type=peer.get('am_type'),
                am_version=peer.get('am_version'))
            self.info("RM-Adaptor=%s" % (adaptor,))

        except Exception as e:
            self.error("do_sdn_action exception: %s" % (str(e),))

    def __do_computing_action(self, peer):
        self.error("Not implemented yet!")
