import amsoil.core.pluginmanager as pm
from se_rm_delegate import SERMGENI3Delegate

def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18447)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = SERMGENI3Delegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("se_rm_geni_v3", handler, "/xmlrpc/geni/3/")
