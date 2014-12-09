import amsoil.core.pluginmanager as pm


def setup():
    from geni3RSpecsManager import Geni3RSpecsManager
    pm.registerService("geni3RSpecsManager", Geni3RSpecsManager)
