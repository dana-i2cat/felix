import amsoil.core.pluginmanager as pm
from monitoring_manager import MonitoringManager
from monitoring_delegate import MonitoringDelegate


def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18449)

    MonitoringManager("0.0.0.0", 18448, True)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = MonitoringDelegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("monitoring_geni_v3", handler, "/monitoring-system/topology/")
