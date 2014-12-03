import amsoil.core.pluginmanager as pm
from tn_rm_delegate import TNRMGENI3Delegate

def setup():
    # setup config keys
    # config = pm.getService("config")

    xmlrpc = pm.getService('xmlrpc')
    handler = pm.getService('geniv3handler')
    delegate = TNRMGENI3Delegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC('tn_rm_geni_v3', handler, '/geni/3')
