import amsoil.core.pluginmanager as pm
from tn_rm_delegate import TNRMGENI3Delegate

def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18446)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = TNRMGENI3Delegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("tn_rm_geni_v3", handler, "/xmlrpc/geni/3/")
