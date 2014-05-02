from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import DBManager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor
from delegate.geni.v3 import exceptions as rms_ex

from lxml.builder import ElementMaker
from lxml import etree

import core
logger = core.log.getLogger("geniv3delegate")

class GENIv3Delegate(GENIv3DelegateBase):
    """
    """
    # TODO should also include a changing component, identified by a config key
    URN_PREFIX = 'urn:RO'

    def __init__(self):
        super(GENIv3Delegate, self).__init__()
        self._resource_manager = rm_adaptor

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'resource-orchestrator': 'http://example.com/resource-orchestrator'}  # /request.xsd

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'resource-orchestrator': 'http://example.com/resource-orchestrator'}  # /manifest.xsd

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'resource-orchestrator': 'http://example.com/resource-orchestrator'}  # /ad.xsd

    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to address single slivers (IPs) rather than
        the whole slice at once."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers (IPs)."""
        return 'geni_many'

    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('It is needed to authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, None, ('listslices',))

        logger.info("Client urn=%s, uuid=%s, email=%s" %
            (client_urn, client_uuid, client_email,))

        # Retrieve the list of configured RMs or peer-RO from the mongoDB
        peers = DBManager().get_all()
        logger.debug("Configured peers=%s" % (peers,))

        # Prepare root for XML tree
        root_node = self.lxml_ad_root()
        E = self.lxml_ad_element_maker("resource-orchestrator")

        # For every peer, try to get the list of available resources
        try:
            for peer in peers:
                logger.debug("peer: %s" % str(peer))
                adaptor = AdaptorFactory.create(type = peer.get('type'),
                                                protocol = peer.get('protocol'),
                                                user = peer.get('user'),
                                                password = peer.get('password'),
                                                address = peer.get('address'),
                                                port = peer.get('port'),
                                                endpoint = peer.get('endpoint'))
                logger.debug("RM-Adapter=%s" % (adaptor,))

#                geni_v3_credentials = [{
#                    "geni_value": credentials,
#                    "geni_version": 3,
#                    "geni_type": "geni_sfa",
#                }]
                # Retrieve credentials alone
                geni_v3_credentials = credentials[0]["geni_value"]

                # Any AM is required to honor the following options
                geni_v3_options = {
                    "geni_available": True,
                    # XXX: it should say 'compressed' (as for GENIv3), not 'compress' (as in AMsoil)
                    # http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#ListResources
                    #"geni_compressed": True,
                    "geni_compress": True,
                    "geni_rspec_version": {
                        "type": "geni",
                        "version": "3",
                    }
                }
                params = [
                    geni_v3_credentials,
                    geni_v3_options,
                ]

                result = adaptor.ListResources(*params)
                r = E.resource()
                # Add retrieved resources to node within XML tree
                r.append(etree.fromstring(result["value"]))
                root_node.append(r)

        # TODO: We need to be more specific here!
        except Exception as e:
            raise geni_ex.GENIv3GeneralError(str(e))

        return self.lxml_to_string(root_node)

    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec, sliver_list = self.status(urns, client_cert, credentials)
        return rspec

    def allocate(self, slice_urn, client_cert, credentials,
                 rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""

        client_urn, client_uuid, client_email = self.auth(client_cert,
                                                          credentials,
                                                          slice_urn,
                                                          ('createsliver',))
        requested_ips = []
        # parse RSpec -> requested_ips
        rspec_root = self.lxml_parse_rspec(rspec)
        for elm in rspec_root.getchildren():
            if not self.lxml_elm_has_request_prefix(elm, 'resource-orchestrator'):
                raise geni_ex.GENIv3BadArgsError("RSpec contains " +
                                                 "elements/namespaces I " +
                                                 "dont understand (%s)." %
                                                 (elm,))

            if (self.lxml_elm_equals_request_tag(elm, 'resource-orchestrator', 'ip')):
                requested_ips.append(elm.text.strip())

            elif (self.lxml_elm_equals_request_tag(elm, 'resource-orchestrator', 'iprange')):
                pass
                # raise geni_ex.GENIv3GeneralError('IP ranges in RSpecs are
                #                                  not supported yet.') # TODO
            else:
                raise geni_ex.GENIv3BadArgsError("RSpec contains an element " +
                                                 "I dont understand (%s)." %
                                                 (elm,))

        reserved_leases = []
        for rip in requested_ips:
            try:
                reserved_leases.append(
                    self._resource_manager.reserve_lease(rip,
                                                         slice_urn,
                                                         client_uuid,
                                                         client_email,
                                                         end_time))
            # translate the resource manager exceptions to GENI exceptions
            except rms_ex.DHCPLeaseNotFound:
                raise geni_ex.GENIv3SearchFailedError("The desired IP(s) " +
                                                      "could no be found " +
                                                      "(%s)." % (rip,))

            except rms_ex.DHCPLeaseAlreadyTaken:
                raise geni_ex.GENIv3AlreadyExistsError("The desired IP(s) is" +
                                                       " already taken (%s)." %
                                                       (rip,))

        # assemble sliver list
        sliver_list = [
            self._get_sliver_status_hash(lease, True, True, "")
            for lease in reserved_leases]

        return (self.lxml_to_string(self._get_manifest_rspec(reserved_leases)),
                sliver_list)

    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # this code is similar to the provision call
        # TODO honor best effort
        leases = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                client_urn, client_uuid, client_email = self.auth(
                    client_cert, credentials, urn,
                    ('renewsliver',))  # authenticate for each given slice
                slice_leases = self._resource_manager.leases_in_slice(urn)
                # extend the lease, so we have a longer timeout.
                for lease in slice_leases:
                    try:
                        self._resource_manager.extend_lease(lease["ip_str"],
                                                            expiration_time)

                    except rms_ex.DHCPMaxLeaseDurationExceeded as e:
                        raise geni_ex.GENIv3BadArgsError("Lease can not be " +
                                                         "extended that long" +
                                                         "(%s)" % (str(e),))

                leases.extend(slice_leases)

            else:
                msg = 'Only slice URNs can be renewed in this aggregate'
                raise geni_ex.GENIv3OperationUnsupportedError(msg)
                # we could use _urn_to_ip helper method for mapping
                # sliver URNs to IPs

        if len(leases) == 0:
            raise geni_ex.GENIv3SearchFailedError("There are no resources " +
                                                  "in the given slice(s)")

        return [
            self._get_sliver_status_hash(lease, True, True, "")
            for lease in leases]

    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        # TODO honor best_effort option
        prov_leases = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                # authenticate for each given slice
                client_urn, client_uuid, client_email = self.auth(
                    client_cert, credentials, urn, ('createsliver',))

                leases = self._resource_manager.leases_in_slice(urn)
                # extend the lease, so we have a longer timeout.
                for lease in leases:
                    try:
                        self._resource_manager.extend_lease(lease["ip_str"],
                                                            end_time)

                    except rms_ex.DHCPMaxLeaseDurationExceeded as e:
                        msg = "Lease can not be extended that long (%s)" %\
                              (str(e),)
                        raise geni_ex.GENIv3BadArgsError(msg)
                # usually you would really instanciate resources here
                # (not necessary for IP-resources)
                prov_leases.extend(leases)

            else:
                msg = 'Only slice URNs can be provisioned by this aggregate'
                raise geni_ex.GENIv3OperationUnsupportedError(msg)
                # we could use _urn_to_ip helper method for mapping
                # sliver URNs to IPs

        if len(prov_leases) == 0:
            msg = "There are no resources in the given slice(s); " +\
                  "perform allocate first"
            raise geni_ex.GENIv3SearchFailedError()
        # assemble return values
        sliver_list = [
            self._get_sliver_status_hash(lease, True, True, "")
            for lease in prov_leases]

        return (self.lxml_to_string(self._get_manifest_rspec(prov_leases)),
                sliver_list)

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # This code is similar to the provision call.
        leases = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                # authenticate for each given slice
                client_urn, client_uuid, client_email = self.auth(
                    client_cert, credentials, urn, ('sliverstatus',))

                slice_leases = self._resource_manager.leases_in_slice(urn)
                leases.extend(slice_leases)

            else:
                msg = "Only slice URNs can be given to status " +\
                      "in this aggregate"
                raise geni_ex.GENIv3OperationUnsupportedError(msg)
                # we could use _urn_to_ip helper method for mapping sliver
                # URNs to IPs

        if len(leases) == 0:
            msg = "There are no resources in the given slice(s)"
            raise geni_ex.GENIv3SearchFailedError(msg)
        # assemble return values
        # logger.info(str(leases))
        sliver_list = [
            self._get_sliver_status_hash(lease, True, True, "")
            for lease in leases]

        return (self.lxml_to_string(self._get_manifest_rspec(leases)),
                sliver_list)

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        # could have similar structure like the provision call
        # You should check for the GENI-default actions like
        # GENIv3DelegateBase.OPERATIONAL_ACTION_xxx
        msg = "DHCP leases do not have operational state."
        raise geni_ex.GENIv3OperationUnsupportedError(msg)

    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # This code is similar to the provision call.
        leases = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                # authenticate for each given slice
                client_urn, client_uuid, client_email = self.auth(
                    client_cert, credentials, urn, ('deletesliver',))

                slice_leases = self._resource_manager.leases_in_slice(urn)
                for lease in slice_leases:
                    self._resource_manager.free_lease(lease["ip_str"])

                leases.extend(slice_leases)
            else:
                msg = 'Only slice URNs can be deleted in this aggregate'
                raise geni_ex.GENIv3OperationUnsupportedError(msg)
                # we could use _urn_to_ip helper method for mapping
                # sliver URNs to IPs

        if len(leases) == 0:
            msg = "There are no resources in the given slice(s)"
            raise geni_ex.GENIv3SearchFailedError(msg)

        # assemble return values
        return [
            self._get_sliver_status_hash(lease, True, True, "")
            for lease in leases]

    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # client_urn, client_uuid, client_email =
        #   self.auth(client_cert, credentials, slice_urn, ('shutdown',))
        raise geni_ex.GENIv3GeneralError("Method not implemented")
        return True

    # Helper methods
    def _ip_to_urn(self, ip_str):
        """Helper method to map IPs to URNs."""
        return ("%s:%s" % (self.URN_PREFIX, ip_str.replace('.', '-')))

    def _urn_to_ip_str(self, urn):
        """Helper method to map URNs to IPs."""
        if (urn.startswith(self.URN_PREFIX)):
            return urn[len(self.URN_PREFIX)+1:].replace('-', '.')
        else:
            msg = "The given URN is not valid for this AM (%s)" % (urn,)
            raise geni_ex.GENIv3BadArgsError(msg)

    def _get_sliver_status_hash(self, lease, include_allocation_status=False,
                                include_operational_status=False,
                                error_message=None):
        """Helper method to create the sliver_status return
        values of allocate and other calls."""
        result = {'geni_sliver_urn': self._ip_to_urn(str(lease["ip_str"])),
                  'geni_expires': lease["end_time"],
                  'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED}

        result['geni_allocation_status'] = self.ALLOCATION_STATE_UNALLOCATED\
            if lease["available"] else self.ALLOCATION_STATE_PROVISIONED

        # there is no state to an ip, so we always return ready
        if (include_operational_status):
            result['geni_operational_status'] = self.OPERATIONAL_STATE_READY

        if (error_message):
            result['geni_error'] = error_message

        return result

    def _get_manifest_rspec(self, leases):
        E = self.lxml_manifest_element_maker('resource-orchestrator')
        manifest = self.lxml_manifest_root()
        for lease in leases:
            # assemble manifest
            r = E.resource()
            r.append(E.ip(lease["ip_str"]))
            # TODO add more info here
from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import DBManager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor
from delegate.geni.v3 import exceptions as rms_ex

from lxml.builder import ElementMaker
from lxml import etree

import core
logger = core.log.getLogger("geniv3delegate")

class GENIv3Delegate(GENIv3DelegateBase):
    """
    """
    # TODO should also include a changing component, identified by a config key
    URN_PREFIX = 'urn:RO'
from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import DBManager
