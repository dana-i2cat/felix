import amsoil.core.pluginmanager as pm
import amsoil.core.log
logger = amsoil.core.log.getLogger('monitoringgeniv3delegate')

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')


class MonitoringDelegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:MONITORING_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/ext/monitoring/3'

    def __init__(self):
        super(MonitoringDelegate, self).__init__()
        logger.info("MonitoringDelegate successfully initialized!")

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        request.xsd"""
        return {'monitoring': 'http://example.com/monitoring'}

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        manifest.xsd"""
        return {'monitoring': self.MANIFEST_URL}

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        ad.xsd"""
        return {'monitoring': 'http://example.com/monitoring'}

    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers."""
        return 'geni_many'

    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")
