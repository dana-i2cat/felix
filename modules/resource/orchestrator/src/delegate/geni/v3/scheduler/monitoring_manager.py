from delegate.geni.v3.db_manager import db_sync_manager
from resource_detector import ResourceDetector
import core
import xml.etree.ElementTree as ET
import requests
logger = core.log.getLogger("monitoring-manager")


class MonitoringManager(ResourceDetector):
    """
    This object can be used to communicate with the MON application.
    """
    def __init__(self):
        super(MonitoringManager, self).__init__("monitoring")

    def physical_info(self):
        self.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            self.debug("Peer=%s" % (peer,))

            root = ET.Element('topology')
            root.attrib['type'] = 'physical'
            # General information
            self.__add_general_info(root)
            # XXX_TODO_XXX: SDN resources

            # XXX_TODO_XXX: C resources

            self.__send(peer, root)

    def __send(self, peer, xml_data):
        try:
            url = "%s://%s:%s/%s" % (peer.get('protocol'), peer.get('address'),
                                     peer.get('port'), peer.get('endpoint'))
            self.info("url=%s" % (url,))
            data = ET.tostring(xml_data)
            self.info("data=%s" % (data,))

            resp = requests.post(url=url,
                                 headers={'Content-Type': 'application/xml'},
                                 data=data).text
            self.info("Resp=%s" % (resp,))

        except Exception as e:
            self.error("Exception: %s" % (e,))

    def __add_general_info(self, root):
        d = ET.SubElement(root, 'domain')
        d.attrib['id'] = db_sync_manager.get_domain_id()
