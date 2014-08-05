from core import log
from core.config import ConfParser
from core.service import Service
import ast

logger = log.getLogger("resource-detector")


class ResourceDetector(Service):
    """
    This object can be used to populate the internal RO's DB
    with the available resources exposed by RMs.
    """
    
    def __init__(self, interval=30):
        self.config = ConfParser("ro.conf")
        self.interval = ast.literal_eval(
                    self.config.get("service \"resource_detector\"").get("interval")
                    )
        super(ResourceDetector, self).__init__("ResourceDetector", self.interval)

    def info(self, msg):
        logger.info("[%s] %s" % (self.name, msg,))

    def do_action(self):
        self.info("[TODO] Periodically retrieving info from RMs...")
