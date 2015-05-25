from core.config import ConfParser
from monitoring.physical_monitoring import PhysicalMonitoring
from monitoring.slice_monitoring import SliceMonitoring
from resource_detector import ResourceDetector

import core
import traceback

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
        self.monitoring_server = {"protocol": self.protocol,
                                    "address": self.address,
                                    "port": self.port,
                                    "endpoint": self.endpoint,
                                }

    def physical_topology(self):
        try:
            return PhysicalMonitoring().send_topology(self.monitoring_server)
        except Exception as e:
            logger.error("Physical topology - Could not send topology. Details: %s" % e)
            logger.error(traceback.format_exc())
    def slice_topology(self):
        return SliceMonitoring().send_topology(self.monitoring_server)

