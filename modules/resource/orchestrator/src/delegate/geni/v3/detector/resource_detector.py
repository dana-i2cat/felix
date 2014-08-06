from delegate.geni.v3.db_manager import DBManager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from core.config import ConfParser
from core.service import Service
import ast

# TODO: can we move these utilities into a proper dir?
import sys
sys.path.insert(0, "../")
from test.utils import calls

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
            result = self.__get_resources(peer)
            if result is None:
                continue
            # decode the Adv RSpec now!
            if peer.get('type') == "sdn_networking":
                self.__decode_sdn_rspec(result)
            elif peer.get('type') == "virtualisation":
                self.__decode_computing_rspec(result)
            else:
                self.error("Unknown peer type=%s" % (peer.get('type'),))

    def __adaptor_create(self, peer):
        return AdaptorFactory.create(
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

    def __credentials(self):
        (text, ucredential) = calls.getusercred(
            user_cert_filename="alice-cert.pem", geni_api=3)
        return ucredential["geni_value"]

    def __get_resources(self, peer):
        try:
            adaptor = self.__adaptor_create(peer)
            self.info("RM-Adaptor=%s" % (adaptor,))

            geni_v3_credentials = self.__credentials()
            return adaptor.list_resources(geni_v3_credentials, False)

        except Exception as e:
            self.error("get_resources (%s) exception: %s" % (
                peer.get('type'), str(e),))
            return None

    def __decode_sdn_rspec(self, result):
        rspec = result.get('value', None)
        if rspec is None:
            self.error("Unable to get RSpec value from %s" % (result,))
            return None

        self.debug("Rspec=%s" % (rspec,))
        return None

    def __decode_computing_rspec(self, result):
        rspec = result.get('value', None)
        if rspec is None:
            self.error("Unable to get RSpec value from %s" % (result,))
            return None

        self.debug("Rspec=%s" % (rspec,))
        return None
