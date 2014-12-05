import amsoil.core.pluginmanager as pm


def setup():
    # Copy rspecs folder
#    import os
#    RSPEC_SRC = os.path.normpath(
#                    os.path.join(
#                        os.path.dirname(__file__), "../../../../../delegate/geni/v3/rspecs/"
#                        )
#                )
#    print "RSPEC_SRC> ", RSPEC_SRC
#    RSPEC_DST = os.path.normpath(
#                    os.path.join(
#                        os.path.dirname(__file__), "../rspecs/"
#                        )
#                )
#    print "RSPEC_DST> ", RSPEC_DST
#
#    import shutil
#    if os.path.isdir(RSPEC_DST):
#        shutil.rmtree(RSPEC_DST)
#    else:
#        shutil.copytree(RSPEC_SRC, RSPEC_DST)

    from geni3RSpecsManager import Geni3RSpecsManager
    pm.registerService("geni3RSpecsManager", Geni3RSpecsManager)
