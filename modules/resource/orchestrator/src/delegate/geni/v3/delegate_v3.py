from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import DBManager
# from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor
# from delegate.geni.v3 import exceptions as rms_ex

from delegate.geni.v3.rspecs.commons import validate
from delegate.geni.v3.rspecs.ro.advertisement_formatter import\
    ROAdvertisementFormatter

# from lxml.builder import ElementMaker
# from lxml import etree

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
        return {'resource-orchestrator':
                'http://example.com/resource-orchestrator'}  # /request.xsd

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'resource-orchestrator':
                'http://example.com/resource-orchestrator'}  # /manifest.xsd

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'resource-orchestrator':
                'http://example.com/resource-orchestrator'}  # /ad.xsd

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
        logger.debug('list_resources: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, None, ('listslices',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("geni_available=%s", geni_available)

        sl = "http://www.geni.net/resources/rspec/3/ad.xsd"
        rspec = ROAdvertisementFormatter(schema_location=sl)
        try:
            logger.debug("OF resources: datapaths")
            for d in DBManager().get_sdn_datapaths():
                rspec.datapath(d)

            logger.debug("OF resources: of-links & fed-links")
            (of_links, fed_links) = DBManager().get_sdn_links()
            for l in of_links:
                rspec.of_link(l)

            for l in fed_links:
                rspec.fed_link(l)

        except Exception as e:
            raise geni_ex.GENIv3GeneralError(str(e))

        logger.debug("RSpec=%s" % (rspec,))
        (result, error) = validate(rspec.get_rspec())
        if result is not True:
            raise geni_ex.GENIv3GeneralError("RSpec validation failure: %s" % (
                                             error,))
        logger.info("List_resources successfully completed!")
        return "%s" % rspec

    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('describe: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ('sliverstatus',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s", urns)
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    # FIXME: Parse RSpec for RO, which should be a GENIv3 RSpec
    # consisting on several nodes of different types
    def allocate(self, slice_urn, client_cert, credentials,
                 rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('allocate: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, slice_urn, ('createsliver',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("slice_urn=%s, end_time=%s, rspec=%s" % (
            slice_urn, end_time, rspec,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('renew: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ('renewsliver',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s, expiration_time=%s, best_effort=%s" % (
            urns, expiration_time, best_effort,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        logger.debug('provision: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ('renewsliver',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s, best_effort=%s, end_time=%s, geni_users=%s" % (
            urns, best_effort, end_time, geni_users,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('status: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ('sliverstatus',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s" % (urns,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        # could have similar structure like the provision call
        # You should check for the GENI-default actions like
        # GENIv3DelegateBase.OPERATIONAL_ACTION_xxx
        logger.debug('perform_op_action: authentication for %s' % (action,))
        if action == "geni_stop":
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urns, ('stopslice',))
        else:
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urns, ('startslice',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s, action=%s, best_effort=%s" % (
            urns, action, best_effort,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('delete: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ('deletesliver',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s, best_effort=%s" % (urns, best_effort,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug('shutdown: authenticate the user...')
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, slice_urn, ('shutdown',))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("slice_urn=%s" % (slice_urn,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    # Helper methods
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
        logger.debug("manifest=%s", (manifest,))
