import amsoil.core.pluginmanager as pm
from ryu_manager import RyuManager
from ryu_delegate import RyuDelegate


def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18450)

    RyuManager("127.0.0.1", 8080)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = RyuDelegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("ryu_geni_v3", handler, "/ryu-not-used")
