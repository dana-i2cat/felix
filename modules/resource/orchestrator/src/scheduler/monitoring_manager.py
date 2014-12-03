from core.config import ConfParser
from monitoring.physical_monitoring import PhysicalMonitoring
#from monitoring.slice_monitoring import SliceMonitoring
from resource_detector import ResourceDetector

import core
import requests

logger = core.log.getLogger("monitoring-manager")


class MonitoringManager(ResourceDetector):
    """
    Periodically communicates both physical and slice data to the MS.
    """

    def __init__(self):
        super(MonitoringManager, self).__init__("monitoring")
        self.config = ConfParser("ro.conf")
        self.monitoring_section = self.config.get("monitoring")
        self.protocol = self.monitoring_section.get("protocol")
        self.address = self.monitoring_section.get("address")
        self.port = self.monitoring_section.get("port")
        self.endpoint = self.monitoring_section.get("endpoint")
        self.monitoring_system = {"protocol": self.protocol,
                                    "address": self.address,
                                    "address": self.address,
                                    "address": self.address
                                }

    def physical_topology(self):
        topology = PhysicalMonitoring().get_topology()
        return self.__send(topology)

    def __send(self, xml_data, peer=None):
        try:
            if not peer:
                peer = self.monitoring_system

            url = "%s://%s:%s/%s" % (peer.get("protocol"), peer.get("address"),
                                     peer.get("port"), peer.get("endpoint"))
            self.info("url=%s" % (url,))
            self.info("data=%s" % (xml_data,))

            reply = requests.post(url=url,
                                 headers={"Content-Type": "application/xml"},
                                 data=xml_data).text
            self.info("Reply=%s" % (reply,))

        except Exception as e:
            self.error("Exception: %s" % (e,))

