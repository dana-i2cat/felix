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

    @staticmethod
    def create(type_, proto, user, pswd, addr, port, ep):
        uri = format_uri(proto, user, pswd, addr, port, ep)

        if type_ == 'virtualisation':
            return CRMAdaptor(uri)

        elif type_ == 'sdn_networking':
            return SDNRMAdaptor(uri)

        raise exceptions.GeneralError("Type not implemented yet!")

    def list_resources(self, credentials, available):
        raise exceptions.GeneralError("This method should be overridden!")


class SFAv2Client(AdaptorFactory):
    def __init__(self, uri):
        AdaptorFactory.__init__(self, uri)
        self.uri_ = uri
        try:
            # Get the required information of the peer
            rspec_version = self.GetVersion()
            values = rspec_version.get('value')
            # We need at least the type and the (supported) request version
            self.type_ = rspec_version.get('code').get('am_type')
            self.req_version_ = values.get('geni_request_rspec_versions')

        except Exception as e:
            raise exceptions.RPCError("SFAv2 GetVersion failure " + str(e))

    def __str__(self):
        return self.uri_

    def format_options(self, available):
        return {'geni_available': available,
                'geni_compressed': False,
                'geni_rspec_version': {'type': self.type_,
                                       'version': self.req_version_}}


class CRMAdaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)

    def list_resources(self, credentials, available):
        options = self.format_options(available)
        try:
            return self.ListResources(credentials, options)

        except Exception as e:
            raise exceptions.RPCError("CRM listResources failure " + str(e))


class SDNRMAdaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)

    def list_resources(self, credentials, available):
        options = self.format_options(available)
        try:
            return self.ListResources(credentials, options)

        except Exception as e:
            raise exceptions.RPCError("SDNRM listResources failure " + str(e))
