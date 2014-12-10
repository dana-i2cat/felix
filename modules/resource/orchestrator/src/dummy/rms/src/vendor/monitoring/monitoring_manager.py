import amsoil.core.log
import bottle
import threading
import socket
from lxml import etree
logger = amsoil.core.log.getLogger("monitoring")


@bottle.post("/monitoring-system/topology/")
def topology():
    logger.info("Request=%s" % (bottle.request))

    if bottle.request.get_header("content-type") != "application/xml":
        bottle.abort(500, "Content-type should be application/xml!")

    body = bottle.request.body.getvalue()
    logger.info("Request.body=%s" % (body))

    topo = etree.fromstring(body)
    logger.info("Topology Info\n\n%s" %
                (etree.tostring(topo, pretty_print=True)))

    return bottle.HTTPResponse(body="Operation completed", status=201)


class MonitoringManager(threading.Thread):
    def __init__(self, address, port, debug):
        super(MonitoringManager, self).__init__(name="monitoring-manager")
        self.daemon = True
        self.address = address
        self.port = port
        self.debug = debug
        super(MonitoringManager, self).start()
        logger.info("MonitoringManager successfully initialized!")

    def is_port_opened(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock.connect_ex((self.address, self.port))

    def run(self):
        if self.is_port_opened() != 0:
            logger.info("Monitoring Manager started at %s:%s" %
                        (self.address, self.port,))
            try:
                bottle.run(server="paste", host=self.address,
                           port=self.port, debug=self.debug)

            except Exception as e:
                logger.error("Exception: %s" % (e,))
        else:
            logger.warning("%s:%s already in use!" % (self.address, self.port))
