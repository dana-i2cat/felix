from amsoil.core import pluginmanager as pm
import geniutil

def setup():
    pm.registerService("geniutil", geniutil)