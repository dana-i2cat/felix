import amsoil.core.pluginmanager as pm
from sdn_rm_delegate import SDNRMGENI3Delegate

def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18443)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = SDNRMGENI3Delegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("sdn_rm_geni_v3", handler, "/xmlrpc/geni/3/")
