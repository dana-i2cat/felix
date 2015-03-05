import amsoil.core.log
import bottle
import threading
import socket
logger = amsoil.core.log.getLogger("ryu")


@bottle.post("/stats/flowentry/add")
def flow_add():
    logger.info("Request=%s" % (bottle.request))

    if bottle.request.get_header("content-type") != "application/json":
        bottle.abort(500, "Content-type should be application/json!")

    body = bottle.request.body.getvalue()
    logger.info("Request.body=%s" % (body))

    return bottle.HTTPResponse(body="Operation completed", status=201)


@bottle.post("/stats/flowentry/delete")
def flow_delete():
    logger.info("Request=%s" % (bottle.request))

    if bottle.request.get_header("content-type") != "application/json":
        bottle.abort(500, "Content-type should be application/json!")

    body = bottle.request.body.getvalue()
    logger.info("Request.body=%s" % (body))

    return bottle.HTTPResponse(body="Operation completed", status=201)


class RyuManager(threading.Thread):
    def __init__(self, address, port):
        super(RyuManager, self).__init__(name="ryu-manager")
        self.daemon = True
        self.address = address
        self.port = port
        super(RyuManager, self).start()
        logger.info("RyuManager successfully initialized!")

    def is_port_opened(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock.connect_ex((self.address, self.port))

    def run(self):
        if self.is_port_opened() != 0:
            logger.info("Ryu Manager started at %s:%s" %
                        (self.address, self.port,))
            try:
                bottle.run(server="paste", host=self.address, port=self.port)

            except Exception as e:
                logger.error("Exception: %s" % (e,))
        else:
            logger.warning("%s:%s already in use!" % (self.address, self.port))
