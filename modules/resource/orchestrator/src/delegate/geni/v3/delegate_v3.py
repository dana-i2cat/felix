from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import DBManager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor

from delegate.geni.v3.rspecs.commons import validate
from delegate.geni.v3.rspecs.commons_of import Match
from delegate.geni.v3.rspecs.ro.advertisement_formatter import\
    ROAdvertisementFormatter
from delegate.geni.v3.rspecs.ro.request_parser import RORequestParser
from delegate.geni.v3.rspecs.ro.manifest_formatter import ROManifestFormatter
from delegate.geni.v3.rspecs.openflow.request_formatter import\
    OFv3RequestFormatter
from delegate.geni.v3.rspecs.openflow.manifest_parser import OFv3ManifestParser

from dateutil import parser as dateparser

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

        logger.debug("ROAdvertisementFormatter=%s" % (rspec,))
        self.__validate_rspec(rspec.get_rspec())

        logger.info("list_resources successfully completed!")
        return "%s" % rspec

    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_manifest, ro_slivers, last_slice = ROManifestFormatter(), [], ""

        for urn in urns:
            logger.debug('describe: authenticate the user for %s' % (urn))
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urn, ('sliverstatus',))

            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        route = DBManager().get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = DBManager().get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get('type') == 'sdn_networking':
                of_m_info, last_slice, of_slivers =\
                    self.__manage_sdn_describe(peer, v, credentials)

                logger.debug("of_m=%s, of_s=%s, urn=%s" %
                             (of_m_info, of_slivers, last_slice))

                ro_manifest.sliver(of_m_info.get('description'),
                                   of_m_info.get('ref'),
                                   of_m_info.get('email'))
                ro_slivers.extend(of_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))
        logger.debug("RO-Slivers=%s" % (ro_slivers,))

        return {'geni_rspec': "%s" % ro_manifest,
                'geni_urn': last_slice,
                'geni_slivers': ro_slivers}

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

        req_rspec = RORequestParser(from_string=rspec)
        self.__validate_rspec(req_rspec.get_rspec())

        ro_manifest, ro_slivers, ro_db_slivers = ROManifestFormatter(), [], []

        sliver = req_rspec.of_sliver()
        if sliver is not None:
            logger.debug("Found an OF-sliver segment: %s", sliver)
            (of_m_info, of_slivers, db_slivers) = self.__manage_sdn_allocate(
                slice_urn, credentials, end_time, sliver, req_rspec)

            logger.debug("of_m=%s, of_s=%s, db_s=%s" %
                         (of_m_info, of_slivers, db_slivers))
            for m in of_m_info:
                ro_manifest.sliver(m.get('description'),
                                   m.get('ref'),
                                   m.get('email'))
            ro_slivers.extend(of_slivers)
            ro_db_slivers.extend(db_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))

        for s in ro_slivers:
            s['geni_expires'] = self.__str2datetime(s['geni_expires'])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))

        logger.debug("RO-DB-Slivers=%s" % (ro_db_slivers,))
        id_ = DBManager().store_slice_info(slice_urn, ro_db_slivers)

        logger.info("allocate successfully completed: %s", id_)
        return ("%s" % ro_manifest, ro_slivers)

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
        ro_slivers, last_slice = [], ""

        for urn in urns:
            logger.debug('status: authenticate the user for %s' % (urn))
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urn, ('sliverstatus',))

            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        route = DBManager().get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = DBManager().get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get('type') == 'sdn_networking':
                last_slice, of_slivers =\
                    self.__manage_sdn_status(peer, v, credentials)

                logger.debug("of_s=%s, urn=%s" % (of_slivers, last_slice))
                ro_slivers.extend(of_slivers)

        for s in ro_slivers:
            s['geni_expires'] = self.__str2datetime(s['geni_expires'])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))
        return last_slice, ro_slivers

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

    def __update_sdn_route(self, route, values):
        for v in values:
            for dpid in v.get('dpids'):
                k = DBManager().get_sdn_datapath_routing_key(dpid)
                dpid['routing_key'] = k
                if k not in route:
                    sl = "http://www.geni.net/resources/rspec/3/request.xsd"
                    route[k] = OFv3RequestFormatter(schema_location=sl)

    def __update_sdn_route_rspec(self, route, sliver, controllers,
                                 groups, matches):
        for key, rspec in route.iteritems():
            rspec.sliver(sliver.get('description'),
                         sliver.get('ref'),
                         sliver.get('email'))
            for c in controllers:
                rspec.controller(c.get('url'), c.get('type'))
            for g in groups:
                rspec.group(g.get('name'))
                for dpid in g.get('dpids'):
                    if dpid.get('routing_key') == key:
                        rspec.group_datapath(g.get('name'), dpid)
            for m in matches:
                match = Match()
                for uf in m.get('use_groups'):
                    match.add_use_group(uf.get('name'))
                for dpid in m.get('dpids'):
                    if dpid.get('routing_key') == key:
                        match.add_datapath(dpid)
                match.set_packet(m.get('packet').get('dl_src'),
                                 m.get('packet').get('dl_dst'),
                                 m.get('packet').get('dl_type'),
                                 m.get('packet').get('dl_vlan'),
                                 m.get('packet').get('nw_src'),
                                 m.get('packet').get('nw_dst'),
                                 m.get('packet').get('nw_proto'),
                                 m.get('packet').get('tp_src'),
                                 m.get('packet').get('tp_dst'))
                rspec.match(match.serialize())

    def __adaptor_create(self, peerDB):
        return AdaptorFactory.create(peerDB.get('type'),
                                     peerDB.get('protocol'),
                                     peerDB.get('user'),
                                     peerDB.get('password'),
                                     peerDB.get('address'),
                                     peerDB.get('port'),
                                     peerDB.get('endpoint'),
                                     peerDB.get('_id'),
                                     peerDB.get('am_type'),
                                     peerDB.get('am_version'))

    def __send_sdn_request_rspec(self, routing_key, of_req_rspec, slice_urn,
                                 credentials, end_time):
        peer = DBManager().get_configured_peer(routing_key)
        logger.debug("Peer=%s" % (peer,))
        adaptor = self.__adaptor_create(peer)
        return adaptor.allocate(slice_urn, credentials[0]["geni_value"],
                                "%s" % of_req_rspec, end_time)

    def __manage_sdn_allocate(self, surn, creds, end, sliver, parser):
        route = {}
        controllers = parser.of_controllers()
        logger.debug("Controllers=%s" % (controllers,))

        groups = parser.of_groups()
        self.__update_sdn_route(route, groups)
        logger.debug("Groups=%s" % (groups,))

        matches = parser.of_matches()
        self.__update_sdn_route(route, matches)
        logger.debug("Matches=%s" % (matches,))

        self.__update_sdn_route_rspec(route, sliver, controllers, groups,
                                      matches)
        logger.info("Route=%s" % (route,))
        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            (m, ss) = self.__send_sdn_request_rspec(k, v, surn, creds, end)
            manifest = OFv3ManifestParser(from_string=m)
            logger.debug("OFv3ManifestParser=%s" % (manifest,))

            sliver = manifest.sliver()
            logger.info("Sliver=%s" % (sliver,))
            manifests.append(sliver)

            logger.info("Slivers=%s" % (ss,))
            slivers.extend(ss)

            for dbs in ss:
                db_slivers.append({
                    'geni_sliver_urn': dbs.get('geni_sliver_urn'),
                    'routing_key': k})

        return (manifests, slivers, db_slivers)

    def __manage_sdn_describe(self, peer, urns, creds):
        adaptor = self.__adaptor_create(peer)
        m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])
        manifest = OFv3ManifestParser(from_string=m)
        logger.debug("OFv3ManifestParser=%s" % (manifest,))

        sliver = manifest.sliver()
        logger.info("Sliver=%s" % (sliver,))

        return (sliver, urn, ss)

    def __manage_sdn_status(self, peer, urns, creds):
        adaptor = self.__adaptor_create(peer)
        urn, ss = adaptor.status(urns, creds[0]["geni_value"])

        return (urn, ss)

    def __validate_rspec(self, generic_rspec):
        (result, error) = validate(generic_rspec)
        if result is not True:
            raise geni_ex.GENIv3GeneralError("RSpec validation failure: %s" % (
                                             error,))
        logger.info("Validation success!")

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    def __str2datetime(self, strval):
        result = dateparser.parse(strval)
        if result:
            result = result - result.utcoffset()
            result = result.replace(tzinfo=None)
        return result

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
