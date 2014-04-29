import xmlrpclib
from delegate.geni.v3 import exceptions


def format_uri(proto, user, pswd, addr, port, ep):
    uri_ = proto + '://'
    if user and pswd:
        uri_ += user + ':' + pswd + '@'

    uri_ += addr + ':' + port + '/' + ep
    return uri_


class AdaptorFactory(xmlrpclib.ServerProxy):
    def __init__(self, uri):
        xmlrpclib.ServerProxy.__init__(self, uri)
        self.uri_ = uri

    def __str__(self):
        return self.uri_

    @staticmethod
    def create(type_, proto, user, pswd, addr, port, ep):
        uri = format_uri(proto, user, pswd, addr, port, ep)

        if type_ == 'virtualisation':
            return CRMAdaptor(uri)

        raise exceptions.GeneralError("Type not implemented yet!")


class CRMAdaptor(AdaptorFactory):
    def __init__(self, uri):
        AdaptorFactory.__init__(self, uri)
