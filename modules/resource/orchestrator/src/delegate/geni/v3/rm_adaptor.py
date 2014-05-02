import xmlrpclib
from delegate.geni.v3 import exceptions

def format_uri(protocol, user, password, address, port, endpoint):
    uri = "%s://" % str(protocol)
    if user and password:
        uri += "%s:%s@" % (str(user), str(password),)

    uri += "%s:%s/%s" % (str(address), str(port), str(endpoint))
    return uri

class AdaptorFactory(xmlrpclib.ServerProxy):
    def __init__(self, uri):
        xmlrpclib.ServerProxy.__init__(self, uri)
        self.uri = uri

    def __str__(self):
        return self.uri

    @staticmethod
    def create(type, protocol, user, password, address, port, endpoint):
        uri = format_uri(protocol, user, password, address, port, endpoint)
        if type == 'virtualisation':
            return CRMAdaptor(uri)
        raise exceptions.GeneralError("Type not implemented yet!")

class CRMAdaptor(AdaptorFactory):
    def __init__(self, uri):
        AdaptorFactory.__init__(self, uri)
