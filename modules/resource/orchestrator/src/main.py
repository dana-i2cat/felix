import sys

from handler.geni.v3.handler_v3 import GENIv3Handler
from delegate.geni.v3.delegate_v3 import GENIv3Delegate

from server.flask.flaskserver import FlaskServer
from server.flask.flaskxmlrpc import FlaskXMLRPC


def main(argv=None):
    if not argv:
        argv = sys.argv

    try:
        # Create and register the RPC server
        flaskserver = FlaskServer()
        xmlrpc = FlaskXMLRPC(flaskserver)

        # GENIv3
        geni_v3_handler = GENIv3Handler()
        geni_v3_delegate = GENIv3Delegate()
        geni_v3_handler.setDelegate(geni_v3_delegate)
        xmlrpc.registerXMLRPC("geni3_ro", geni_v3_handler, "/geni/3")

        # Run server
        flaskserver.runServer()

    except KeyboardInterrupt:
        return True

    except Exception as ex:
        print >>sys.stderr, "Got an exception: " + str(ex)
        return False

    return True


if __name__ == '__main__':
        sys.exit(main())
