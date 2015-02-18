from flask import Flask, g, request, request_started, request_finished
from flask.ext.pymongo import PyMongo

from core.config import ConfParser
from core import log
logger=log.getLogger("flaskserver")
from server.flask.views import ro_flask_views

from werkzeug import serving
from OpenSSL import SSL, crypto

import ast

class ClientCertHTTPRequestHandler(serving.WSGIRequestHandler):
    """Overwrite the werkzeug handler, so we can extract the client cert and put it into the request's environment."""
    def make_environ(self):
        env = super(ClientCertHTTPRequestHandler, self).make_environ()
        if self._client_cert:
            env['CLIENT_RAW_CERT'] = self._client_cert
        return env

    def setup(self):
        super(ClientCertHTTPRequestHandler, self).setup()
        self.connection.do_handshake()
        peer_cert = self.connection.get_peer_certificate()
        if peer_cert:
            pem = crypto.dump_certificate(crypto.FILETYPE_PEM, peer_cert)
            self._client_cert = pem
        else:
            self._client_cert = None

class FlaskServer(object):
    """
    Encapsules a flask server instance.
    It also exports/defines the rpcservice interface.

    When a request comes in the following chain is walked through:
        --http--> nginx webserver --fcgi--> WSGIServer --WSGI--> FlaskApp
    When using the development server:
        werkzeug server --WSGI--> FlaskApp
    """

    def __init__(self):
        """Constructor for the server wrapper."""
        #self._app = Flask(__name__) # imports the named package, in this case this file
        # Imports the named module (package includes "." and this is not nice with PyMongo)
        self.config = ConfParser("flask.conf")
        self.general_section = self.config.get("general")
        self.template_folder = self.general_section.get("template_folder")
        self.fcgi_section = self.config.get("fcgi")
        self.certificates_section = self.config.get("certificates")
        self._app = Flask(__name__.split(".")[-1], template_folder = self.template_folder)
        self._mongo = PyMongo(self._app)
        # Added in order to be able to execute "before_request" method
        app = self._app

        # Setup debugging for app
        cDebug = self.general_section.get("debug")
        if cDebug: # log all actions on the XML-RPC interface
            def log_request(sender, **extra):
                logger.info(">>> REQUEST %s:\n%s" % (request.path, request.data))
            request_started.connect(log_request, self._app)
            def log_response(sender, response, **extra):
                logger.info(">>> RESPONSE %s:\n%s" % (response.status, response.data))
            request_finished.connect(log_response, self._app)

        @app.before_request
        def before_request():
            # "Attach" objects within the "g" object. This is passed to each view method
            g.mongo = self._mongo

    @property
    def app(self):
        """Returns the flask instance (not part of the service interface, since it is specific to flask)."""
        return self._app

    def add_routes(self):
        """
        New method. Allows to register URLs from a the views file.
        """
#        from server.flask import views as flask_views
#        flask_views_custom_methods = filter(lambda x: x.startswith("view_"), dir(flask_views))
#        for custom_method in flask_views_custom_methods:
#            # Retrieve data needed to add the URL rule to the Flask app
#            view_method = getattr(locals()["flask_views"], custom_method)
#            docstring = getattr(view_method, "__doc__")
#            index_start = docstring.index("@app.route")
#            index_end = index_start + len("@app.route") + 1
#            custom_method_url = docstring[index_end:].replace(" ","").replace("\n","")
#            # Get: (a) method URL to bind flask app, (b), method name, (c) method object to invoke
#            self._app.add_url_rule(custom_method_url, custom_method, view_func=view_method(self._mongo))
        self._app.register_blueprint(ro_flask_views)

    def runServer(self, services=[]):
        """Starts up the server. It (will) support different config options via the config plugin."""
        self.add_routes()
        debug = self.general_section.get("debug")
        host = self.general_section.get("host")
        use_reloader = ast.literal_eval(self.general_section.get("use_reloader"))
        app_port = int(self.general_section.get("port"))
        template_folder = self.general_section.get("template_folder")
        cFCGI = ast.literal_eval(self.fcgi_section.get("enabled"))
        fcgi_port = int(self.fcgi_section.get("port"))
        must_have_client_cert = ast.literal_eval(self.certificates_section.get("force_client_certificate"))
        if cFCGI:
            logger.info("registering fcgi server at %s:%i", host, fcgi_port)
            from flup.server.fcgi import WSGIServer
            WSGIServer(self._app, bindAddress=(host, fcgi_port)).run()
        else:
            logger.info("registering app server at %s:%i", host, app_port)
            # this workaround makes sure that the client cert can be acquired later (even when running the development server)
            # copied all this stuff from the actual flask implementation, so we can intervene and adjust the ssl context
            # self._app.run(host=host, port=app_port, ssl_context='adhoc', debug=debug, request_handler=ClientCertHTTPRequestHandler)

            # the code from flask's `run...`
            # see https://github.com/mitsuhiko/flask/blob/master/flask/app.py
            options = {}
            try:
                # now the code from werkzeug's `run_simple(host, app_port, self._app, **options)`
                # see https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/serving.py
                from werkzeug.debug import DebuggedApplication
                import socket
                application = DebuggedApplication(self._app, True)
                def inner():
                    server = serving.make_server(host, app_port, self._app, False, 1, ClientCertHTTPRequestHandler, False, 'adhoc')
                    # The following line is the reason why I copied all that code!
                    if must_have_client_cert:
                        # FIXME: what works with web app does not work with cli. Check this out
                        server.ssl_context.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, lambda a,b,c,d,e: True)
                    # before enter in the loop, start the supplementary services
                    for s in services:
                        s.start()
                    # That's it
                    server.serve_forever()
                address_family = serving.select_ip_version(host, app_port)
                test_socket = socket.socket(address_family, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind((host, app_port))
                test_socket.close()
                # Disable reloader only by explicit config setting
                if use_reloader == False:
                    serving.run_simple(host, app_port, self._app, use_reloader=False)
                else:
                    serving.run_with_reloader(inner, None, 1)
            finally:
                self._app._got_first_request = False
