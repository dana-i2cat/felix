from handler.geni.v3.computing.computing_handler_v3 import GENIv3Handler as GENIv3CRMHandler
from delegate.geni.v3.computing.computing_delegate_v3 import ComputingGENI3Delegate as GENIv3CRMDelegate
from handler.geni.v3.sdn.sdn_handler_v3 import GENIv3Handler as GENIv3SDNRMHandler
from delegate.geni.v3.sdn.sdn_delegate_v3 import SDNGENI3Delegate as GENIv3SDNRMDelegate

from server.flask.flaskserver import FlaskServer
from server.flask.flaskxmlrpc import FlaskXMLRPC

if __name__ == "__main__":
    # Create and register the RPC server
    flaskserver = FlaskServer()
    xmlrpc = FlaskXMLRPC(flaskserver)
    
    ## Computing RM
    # GENIv3
    geni_v3_computing_handler = GENIv3CRMHandler()
    geni_v3_computing_delegate = GENIv3CRMDelegate()
    geni_v3_computing_handler.setDelegate(geni_v3_computing_delegate)
    xmlrpc.registerXMLRPC("geni3_crm", geni_v3_computing_handler, "/geni/3/computing")

    ## Software-Defined Networking RM
    # GENIv3
    geni_v3_sdn_handler = GENIv3SDNRMHandler()
    geni_v3_sdn_delegate = GENIv3SDNRMDelegate()
    geni_v3_sdn_handler.setDelegate(geni_v3_sdn_delegate)
    xmlrpc.registerXMLRPC("geni3_sdnrm", geni_v3_sdn_handler, "/geni/3/sdn")

    # Run server
    flaskserver.runServer()
