import sys

from delegate.geni.v3.delegate_v3 import GENIv3Delegate
from delegate.geni.v3.se_scheduler import SESchedulerService
from handler.geni.v3.handler_v3 import GENIv3Handler
from server.flask.flaskserver import FlaskServer
from server.flask.flaskxmlrpc import FlaskXMLRPC
import logging
logging.basicConfig()


def main(argv=None):
    if not argv:
        argv = sys.argv
    # Try to handle unexpected exceptions
    try:
        # Create and register the RPC server
        flaskserver = FlaskServer()
        xmlrpc = FlaskXMLRPC(flaskserver)
        
        se_scheduler = SESchedulerService()
        #se_scheduler.start()
        
        # GENIv3
        geni_v3_handler = GENIv3Handler()
        geni_v3_delegate = GENIv3Delegate()
        geni_v3_handler.setDelegate(geni_v3_delegate)
        xmlrpc.registerXMLRPC("geni3_se", geni_v3_handler, "/xmlrpc/geni/3/")
        # Services/Workers to add
        # Topology update
        print "^^^^^^^^^^"
        
        print "$$$$$$$$"
        # Run server starting the services
        flaskserver.runServer()
        print "********"
    except KeyboardInterrupt:
        return True
    except Exception as e:
        sys.stderr.write("Got an exception: %s" % str(e))
        return False
    finally:
        pass
        # Stop the services
        se_scheduler.stop()
    return True


if __name__ == '__main__':
    # Adding paths to server
    # sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    sys.exit(main())
