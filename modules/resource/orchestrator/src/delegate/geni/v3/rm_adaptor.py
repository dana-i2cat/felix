import xmlrpclib
from lxml import etree
from delegate.geni.v3 import exceptions
from delegate.geni.v3.db_manager import DBManager
from models.c_resource_table import CResourceTable

import core
logger = core.log.getLogger("rmadaptor")


def format_uri(protocol, user, password, address, port, endpoint):
    uri = "%s://" % str(protocol)
    if user and password:
        uri += "%s:%s@" % (str(user), str(password),)

    uri += "%s:%s/%s" % (str(address), str(port), str(endpoint))
    return uri


class AdaptorFactory(xmlrpclib.ServerProxy):
    def __init__(self, uri):
        xmlrpclib.ServerProxy.__init__(self, uri)

    @staticmethod
    def get_am_info(uri, id):
        client = SFAClient(uri)
        (type, version) = client.get_version()
        DBManager().update_am_info(id, type, version)
        return (type, version)

    @staticmethod
    def create(type, protocol, user, password, address, port, endpoint,
               id, am_type, am_version):
        uri = format_uri(protocol, user, password, address, port, endpoint)
        if am_type is None or am_version is None:
            logger.debug("We need to update the AM info for this RM...")
            (am_type, am_version) = AdaptorFactory.get_am_info(uri, id)

        if am_type in ['geni', 'geni_sfa', 'sfa'] and am_version <= 2:
            if type == 'virtualisation':
                return CRMGeniv2Adaptor(uri)
            elif type == 'sdn_networking':
                return SDNRMGeniv2Adaptor(uri)

        raise exceptions.GeneralError("Type not implemented yet!")


class SFAClient(AdaptorFactory):
    def __init__(self, uri, type=None, version=None):
        AdaptorFactory.__init__(self, uri)
        self.uri = uri
        self.geni_type = type
        self.geni_api_version = version

    def get_version(self):
        try:
            # Get the required information of the peer
            rspec_version = self.GetVersion()
            logger.debug("Rspec version: %s" % (rspec_version,))
            values = rspec_version.get('value')
            # We need at least the type and the (supported) request version
            self.geni_type = rspec_version.get('code').get('am_type')
            self.geni_api_version = values.get('geni_api')

            return (self.geni_type, self.geni_api_version)

        except Exception as e:
            raise exceptions.RPCError("SFA GetVersion failure: %s" % str(e))

    def list_resources(self, credentials, available):
        raise exceptions.GeneralError("This method should be overridden!")

    def __str__(self):
        return "[%s, %s, %s]" %\
            (self.uri, self.geni_type, self.geni_api_version)

    def api_version(self):
        return self.geni_api_version

    def sfa_type(self):
        return self.geni_type


class SFAv2Client(SFAClient):
    def __init__(self, uri):
        SFAClient.__init__(self, uri, type='sfa', version=2)

    def format_options(self, available):
        return {"geni_available": available,
                "geni_compress": False,
                "geni_rspec_version": {
                    "type": self.geni_type,
                    "version": self.geni_api_version, }}


class CRMGeniv2Adaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)

    def __filter_list_resources_rspec(self, rspec):
        root = etree.fromstring(rspec.get('value'))
        # logger.debug("ROOT: %s" % (etree.tostring(root, pretty_print=True),))
        for network in root.iter('network'):
            for node in network.iter('node'):
                # Follow the schema proposed into the models
                entry = CResourceTable()
                entry.network_name(network.get('name'))
                entry.node(node.get('component_id'),
                           node.get('component_manager_id'),
                           node.get('component_name'),
                           node.get('exclusive'))
                entry.hostname(node.findtext('hostname'))
                entry.name(node.findtext('name'))
                logger.debug("Entry: %s" % (entry,))

                for service in node.iter('service'):
                    entry.clear_services()
                    # Filter on the service type
                    service_type = service.get('type')
                    if service_type == "Range":
                        entry.add_range_service(
                            service.findtext('type'),
                            service.findtext('name'),
                            service.findtext('start_value'),
                            service.findtext('end_value'))
                        # Log the Range Entry
                        logger.debug("Range Entry: %s" % (entry,))

                    elif service_type == "NetworkInterface":
                        entry.add_netif_service(
                            service.findtext('from_server_interface_name'),
                            service.findtext('to_network_interface_id'),
                            service.findtext('to_network_interface_port'))
                        # Log the NetworkInterface info
                        logger.debug("NetworkInterface Entry: %s" % (entry,))

                    if entry.is_reserved():
                        logger.info("Modify the rspec: delete this service!")
                        node.remove(service)

                if node.find('service') is None:
                    logger.info("No more services are available on this node!")
                    network.remove(node)

        rspec['value'] = etree.tostring(root)
        # logger.debug("RSPEC: %s" % (rspec,))
        return rspec

    def list_resources(self, credentials, available):
        options = self.format_options(available)
        logger.debug("Options: %s" % (options,))
        try:
            # Get the list of computing resources
            params = [credentials, options, ]
            rspec = self.ListResources(*params)
            # if available==True, we should remove the computing
            # "local reserved" resources (stored in a mongoDB table)
            if available is True:
                rspec = self.__filter_list_resources_rspec(rspec)

            return rspec

        except Exception as e:
            raise exceptions.RPCError("CRMGeniv2 ListResources failure: %s" %
                                      str(e))


class SDNRMGeniv2Adaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)

    def __decode_list_resources_rspec(self, rspec):
        logger.error("XXX_TODO_XXX: loop and clear if needed!")
        return rspec

    def list_resources(self, credentials, available):
        options = self.format_options(available)
        logger.debug("Options: %s" % (options,))
        try:
            # Get the list of sdn networking resources
            params = [credentials, options, ]
            rspec = self.ListResources(*params)
            # if available==True, we should remove the sdn networking
            # "local reserved" resources (stored in a mongoDB tables)
            if available is True:
                rspec = self.__decode_list_resources_rspec(rspec)

            return rspec

        except Exception as e:
            raise exceptions.RPCError("SDNRMGeniv2 ListResources failure: %s" %
                                      str(e))
