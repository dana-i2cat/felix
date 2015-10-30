from core import dates
from core.peers import AllowedPeers
from core.utils.urns import URNUtils
from delegate.geni.v3.base import GENIv3DelegateBase
from db.db_manager import db_sync_manager
# Following import cannot be ordered properly
from delegate.geni.v3 import rm_adaptor
from scheduler.jobs import slice_expiration
from scheduler.ro_scheduler import ROSchedulerService
from rspecs.ro.advertisement_formatter import ROAdvertisementFormatter
from rspecs.ro.manifest_formatter import ROManifestFormatter
from rspecs.ro.request_parser import RORequestParser
from handler.geni.v3 import exceptions as geni_ex

from monitoring.slice_monitoring import SliceMonitoring
from utils.commons import CommonUtils
# Import utils to parse/format specific resources
from utils.com import COMUtils
from utils.sdn import SDNUtils
from utils.se import SEUtils
from utils.tn import TNUtils
from utils.ro import ROUtils

from mapper.path_finder_tn_to_sdn import PathFinderTNtoSDN

from core.config import ConfParser
import ast
import core

logger = core.log.getLogger("geniv3delegate")


class GENIv3Delegate(GENIv3DelegateBase):
    """
    Note: 'geni_expires' keys are returned as a python datetime object
    to the handler in the upper layer. This will convert them to strings
    """
    # TODO should also include a changing component, identified by a config key
    URN_PREFIX = "urn:RO"

    def __init__(self):
        super(GENIv3Delegate, self).__init__()
        self._resource_manager = rm_adaptor
        self._verify_users =\
            ast.literal_eval(ConfParser("geniv3.conf").get("certificates").
                             get("verify_users"))
        self._allowed_peers = AllowedPeers.get_peers()
        self._mro_enabled =\
            ast.literal_eval(ConfParser("ro.conf").get("master_ro").
                             get("mro_enabled"))

    def trace_method_inputs(f):
        as_ = f.func_code.co_varnames[:f.func_code.co_argcount]

        def wrapper(*args, **kwargs):
            ass_ = ', '.join('%s=%r' % e for e in zip(as_, args) +
                             kwargs.items())
            logger.info("Calling %s with args=%s" % (f.func_name, ass_,))
            return f(*args, **kwargs)
        return wrapper

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"resource-orchestrator":
                "http://example.com/resource-orchestrator"}  # /request.xsd

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"resource-orchestrator":
                "http://example.com/resource-orchestrator"}  # /manifest.xsd

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"resource-orchestrator":
                "http://example.com/resource-orchestrator"}  # /ad.xsd

    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to address single slivers (IPs) rather than
        the whole slice at once."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers (IPs)."""
        return "geni_many"

    @trace_method_inputs
    def list_resources(self, client_cert, credentials, geni_available):
        """
        Shows a list with the slivers managed or seen by the resource manager.

        @param client_cert client certificate (X509)
        @param credentials client credential(s), provided by the ClearingHouse
            and generated after the certificates
        @param geni_available flag to describe which slivers are expected
            to be shown
                * geni_available = True : only available (non-allocated,
                                          non-provisioned) will be shown
                * geni_available = False : every slivers will be shown
        @return rspec RSpec document containing a list of the slivers,
            formatted in accordance to GENI schemas
        """

        if self._verify_users:
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, None, ("listslices",))
            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        logger.info("geni_available=%s", geni_available)

        sl = "http://www.geni.net/resources/rspec/3/ad.xsd"
        rspec = ROAdvertisementFormatter(schema_location=sl)

        try:
            for n in db_sync_manager.get_com_nodes():
                logger.debug("COMresources node=%s" % (n,))
                rspec.com_node(n)

            for d in db_sync_manager.get_sdn_datapaths():
                logger.debug("OFresources dpid=%s" % (d,))
                rspec.datapath(d)

            for n in db_sync_manager.get_tn_nodes():
                logger.debug("TNresources node=%s" % (n,))
                rspec.tn_node(n)

            for n in db_sync_manager.get_se_nodes():
                logger.debug("SEresources node=%s" % (n,))
                rspec.se_node(n)

            for l in db_sync_manager.get_com_links():
                logger.debug("COMresources link=%s" % (l,))
                rspec.com_link(l)

            (of_links, fed_links) = db_sync_manager.get_sdn_links()
            for l in of_links:
                logger.debug("OFresources of-link=%s" % (l,))
                rspec.of_link(l)

            for l in fed_links:
                logger.debug("OFresources fed-link=%s" % (l,))
                rspec.fed_link(l)

            for l in db_sync_manager.get_tn_links():
                logger.debug("TNresources tn-link=%s" % (l,))
                rspec.tn_link(l)

            for l in db_sync_manager.get_se_links():
                logger.debug("SEresources se-link=%s" % (l,))
                rspec.se_link(l)

        except Exception as e:
            raise geni_ex.GENIv3GeneralError(str(e))

        logger.debug("ROAdvertisementFormatter=%s" % (rspec,))
        CommonUtils().validate_rspec(rspec.get_rspec())
        return "%s" % rspec

    @trace_method_inputs
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_manifest, ro_slivers, last_slice = ROManifestFormatter(), [], ""

        if self._verify_users:
            for urn in urns:
                logger.debug("describe: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == self._allowed_peers.get("PEER_SDNRM"):
                of_m_info, last_slice, of_slivers =\
                    SDNUtils().manage_describe(peer, v, credentials)

                logger.debug("of_m=%s, of_s=%s, urn=%s" %
                             (of_m_info, of_slivers, last_slice))
                for s in of_m_info.get("slivers"):
                    ro_manifest.of_sliver(s)

                ro_slivers.extend(of_slivers)

            elif peer.get("type") == self._allowed_peers.get("PEER_TNRM"):
                tn_m_info, last_slice, tn_slivers =\
                    TNUtils().manage_describe(peer, v, credentials)

                logger.debug("tn_m=%s, tn_s=%s, urn=%s" %
                             (tn_m_info, tn_slivers, last_slice))
                for n in tn_m_info.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in tn_m_info.get("links"):
                    ro_manifest.tn_link(l)

                ro_slivers.extend(tn_slivers)

            elif peer.get("type") == self._allowed_peers.get("PEER_SERM"):
                se_m_info, last_slice, se_slivers =\
                    SEUtils().manage_describe(peer, v, credentials)

                logger.debug("se_m=%s, se_s=%s, urn=%s" %
                             (se_m_info, se_slivers, last_slice))
                for n in se_m_info.get("nodes"):
                    ro_manifest.se_node(n)
                for l in se_m_info.get("links"):
                    ro_manifest.se_link(l)

                ro_slivers.extend(se_slivers)

            elif peer.get("type") == self._allowed_peers.get("PEER_CRM"):
                com_m_info, last_slice, com_slivers =\
                    COMUtils().manage_describe(peer, v, credentials)

                logger.debug("com_m=%s, com_s=%s, urn=%s" %
                             (com_m_info, com_slivers, last_slice))
                for n in com_m_info.get("nodes"):
                    ro_manifest.com_node(n)
                ro_slivers.extend(com_slivers)

            elif peer.get("type") == self._allowed_peers.get("PEER_RO"):
                ro_m_info, last_slice, ro_slivers_ro =\
                    ROUtils().manage_describe(peer, v, credentials)

                logger.debug("ro_m=%s, ro_s=%s, urn=%s" %
                             (ro_m_info, ro_slivers, last_slice))
                ro_manifest = ROUtils.generate_describe_manifest(
                    ro_manifest, ro_m_info)
                ro_slivers.extend(ro_slivers_ro)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))
        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(ro_slivers)

        return {"geni_rspec": "%s" % ro_manifest,
                "geni_urn": last_slice,
                "geni_slivers": ro_slivers}

    @trace_method_inputs
    def allocate(self, slice_urn, client_cert, credentials,
                 rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        if self._verify_users:
            logger.debug("allocate: authenticate the user...")
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials,
                          slice_urn, ("createsliver",))
            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        logger.info("slice_urn=%s, end_time=%s, rspec=%s" % (
            slice_urn, end_time, rspec,))

        req_rspec = RORequestParser(from_string=rspec)
        CommonUtils().validate_rspec(req_rspec.get_rspec())

        ro_manifest, ro_slivers, ro_db_slivers = ROManifestFormatter(), [], []

        # Before starting the allocation process, we need to find a proper
        # mapping between TN and SDN resources in the islands.
        # We use the tn-links as starting point (STPs)
        stps = TNUtils().find_stps_from_links(req_rspec.tn_links())
        logger.debug("STPs=%s" % (stps,))
        dpid_port_ids = SDNUtils().find_dpid_port_identifiers(
            req_rspec.of_groups(), req_rspec.of_matches())
        logger.debug("DPIDs=%s" % (dpid_port_ids,))

        extend_groups = []
        # If MRO: run mapper path-finder to extend SDN resources
        # by adding an inherent link to the SE device
        if self._mro_enabled:
            for stp in stps:
                path_finder_tn_sdn = PathFinderTNtoSDN(
                    stp.get("src_name"), stp.get("dst_name"))
                paths = path_finder_tn_sdn.find_paths()
                logger.info("PATHs=%s" % (paths,))
                # XXX Mapper: raise an exception when a path *between different authorities/islands* cannot be found
                src_auth = URNUtils.get_felix_authority_from_urn(stp.get("src_name"))
                dst_auth = URNUtils.get_felix_authority_from_urn(stp.get("dst_name"))
                # TODO FIXME Check why no mapping is provided between two STPs within the same island
                # TODO FIXME Remove 1st condition after fixing that in the mapper
                if src_auth != dst_auth and len(paths) == 0:
                    e = "Mapper SDN-SE-TN: received empty path. Possible causes: requested STPs are disconnected and/or located in the same island"
                    raise geni_ex.GENIv3GeneralError(e)
                items = SDNUtils().analyze_mapped_path(dpid_port_ids, paths)
                extend_groups.extend(items)

            logger.warning("Request RSpec must be extended with SDN-groups: %s" %
                       (extend_groups,))

        # COM resources
        slivers = req_rspec.com_slivers()
        nodes = req_rspec.com_nodes()
        if slivers:
            logger.debug("Found a COM-slivers segment (%d): %s" %
                         (len(slivers), slivers,))
            (com_m_info, com_slivers, db_slivers) =\
                COMUtils().manage_allocate(slice_urn, credentials, end_time,
                                           slivers, req_rspec)

            logger.debug("com_m=%s, com_s=%s, com_s=%s" %
                         (com_m_info, com_slivers, db_slivers))
            for m in com_m_info:
                for n in m.get("nodes"):
                    ro_manifest.com_node(n)

            ro_slivers.extend(com_slivers)
            # insert com-resources into slice table
            self.__insert_slice_info(
                "com-resources", slice_urn, db_slivers, ro_db_slivers)

        # SDN resources
        se_sdn_info = None
        sliver = req_rspec.of_sliver()
        if sliver is not None:
            logger.debug("Found an SDN-sliver segment: %s", sliver)
            # Manage the "extend-group" info here: extend the group info
            # introducing the new dpids/ports taken from
            # the mapper (path-finder) module.
            (of_m_info, of_slivers, db_slivers, se_sdn_info) =\
                SDNUtils().manage_allocate(
                    slice_urn, credentials, end_time, sliver, req_rspec,
                    slice_urn, extend_groups)

            logger.debug("sdn_m=%s, sdn_s=%s, db_s=%s" %
                         (of_m_info, of_slivers, db_slivers))
            for m in of_m_info:
                for s in m.get("slivers"):
                    ro_manifest.of_sliver(s)

            ro_slivers.extend(of_slivers)
            # insert sdn-resources into slice table
            self.__insert_slice_info(
                "sdn-resources", slice_urn, db_slivers, ro_db_slivers)

        # TN resources
        se_tn_info = None
        nodes = req_rspec.tn_nodes()
        links = req_rspec.tn_links()
        if (len(nodes) > 0) or (len(links) > 0):
            logger.debug("Found a TN-nodes segment (%d): %s" %
                         (len(nodes), nodes,))
            logger.debug("Found a TN-links segment (%d): %s" %
                         (len(links), links,))
            (tn_m_info, tn_slivers, db_slivers, se_tn_info) =\
                TNUtils().manage_allocate(slice_urn, credentials, end_time,
                                          nodes, links)

            logger.debug("tn_m=%s, tn_s=%s, db_s=%s" %
                         (tn_m_info, tn_slivers, db_slivers))
            for m in tn_m_info:
                for n in m.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in m.get("links"):
                    ro_manifest.tn_link(l)

            ro_slivers.extend(tn_slivers)
            # insert tn-resources into slice table
            self.__insert_slice_info(
                "tn-resources", slice_urn, db_slivers, ro_db_slivers)

        # SE resources
        se_nodes_in_request = False
        try:
            # SE resources (specifically in request)
            nodes = req_rspec.se_nodes()
            links = req_rspec.se_links()
            if ((len(nodes) > 0) or (len(links) > 0)):
                se_nodes_in_request = True
            else:
                raise Exception("No SE nodes or links available in the request")
        except Exception as e:
            logger.warning("No SE resources found in request. Switching to automatic generation. Details: %s" % str(e))
            # SE resources (generated by RO from SE and TN nodes)
            if (se_sdn_info is not None) and (len(se_sdn_info) > 0) and\
               (se_tn_info is not None) and (len(se_tn_info) > 0):
                nodes = se_sdn_info
                links = se_tn_info

        # Common code to process SE nodes, either found or generated
        # [Previous comment] (?) This is an extension provided to allow MRO-RO
        # interoperability and could be very useful for testing & debugging, too...
        if (len(nodes) > 0) or (len(links) > 0):
            logger.debug("Found a SE-node segment (%d): %s" %
                         (len(nodes), nodes,))
            logger.debug("Found a SE-link segment (%d): %s" %
                         (len(links), links,))
            if se_nodes_in_request:
                (se_m_info, se_slivers, db_slivers) =\
                    SEUtils().manage_direct_allocate(
                        slice_urn, credentials, end_time, nodes, links)
            else:
                (se_m_info, se_slivers, db_slivers) =\
                    SEUtils().manage_allocate(slice_urn, credentials, end_time,
                                            nodes, links)

            logger.debug("se_m=%s, se_s=%s, db_s=%s" %
                         (se_m_info, se_slivers, db_slivers))
            for m in se_m_info:
                for n in m.get("nodes"):
                    ro_manifest.se_node(n)
                for l in m.get("links"):
                    ro_manifest.se_link(l)

            ro_slivers.extend(se_slivers)
            # insert se-resources into slice table
            self.__insert_slice_info(
                "se-resources", slice_urn, db_slivers, ro_db_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))
        CommonUtils().validate_rspec(ro_manifest.get_rspec())

        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(ro_slivers)

        logger.info("Allocate successfully completed: %s" % (ro_db_slivers,))
        self.__schedule_slice_release(end_time, ro_db_slivers)
        return ("%s" % ro_manifest, ro_slivers)

    @trace_method_inputs
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        """
        Renews the sliver(s) requested to a given date, passed by the user.
        The new expiration date for the sliver(s) must be less or equal to the
        expiration date of the user's credential.
        When best_effort is enabled, renewal will be attempted on every
        resource.

        @param urns list of URNs with the identifiers of the resources
            to be treated
        @param client_cert client certificate (X509)
        @param credentials client credential(s), provided by the ClearingHouse
            and generated after the certificates
        @param expiration_time new expiration date for the selected sliver(s).
            Must comply to rfr3339 format
        @param best_effort flag to describe the behaviour upon a failure
                * best_effort = True : as much operations as possible are
                                       performed upon an error condition
                * best_effort = False : the set of operations will be stopped
                                        if an error occurs
        @return ro_slivers structure containing information of slivers
            (URN, expiration date, etc)
        """
        ro_slivers = []

        if self._verify_users:
            for urn in urns:
                logger.debug("renew: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("renewsliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        logger.info("expiration_time=%s, best_effort=%s" % (
            expiration_time, best_effort,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        etime_str = dates.datetime_to_rfc3339(expiration_time)
        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") in self._allowed_peers.values():
                slivers = CommonUtils().manage_renew(
                    peer, v, credentials, etime_str, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(ro_slivers)

        return ro_slivers

    @trace_method_inputs
    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is relevant here."""
        ro_manifest, ro_slivers = ROManifestFormatter(), []
        client_urn = CommonUtils.fetch_user_name_from_geni_users(geni_users)
        if self._verify_users:
            for urn in urns:
                logger.debug("provision: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("createsliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        slice_urn = db_sync_manager.get_slice_urn(urns)
        slice_monitor = None
        try:
            slice_monitor = SliceMonitoring()
            slice_monitor.add_topology(slice_urn, SliceMonitoring.PROVISIONED,
                                       client_urn)
        except Exception as e:
            logger.warning("Delegate could not send Provision trigger" +
                           " to MS. Details: %s", (e,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == self._allowed_peers.get("PEER_CRM"):
                com_m_info, com_slivers = COMUtils().manage_provision(
                    peer, v, credentials, best_effort, end_time, geni_users)

                logger.debug("com_m=%s, com_s=%s" % (com_m_info, com_slivers,))
                for n in com_m_info.get("nodes"):
                    ro_manifest.com_node(n)

                ro_slivers.extend(com_slivers)
                # introduce slice-monitoring info for C resources
                try:
                    slice_monitor.add_c_resources(
                        slice_urn, com_m_info.get("nodes"))
                except Exception as e:
                    logger.warning("Delegate could not monitor COM resources" +
                                   " upon Provision. Details: %s", (e,))

            elif peer.get("type") == self._allowed_peers.get("PEER_SDNRM"):
                of_m_info, of_slivers = SDNUtils().manage_provision(
                    peer, v, credentials, best_effort, end_time, geni_users)

                logger.debug("of_m=%s, of_s=%s" % (of_m_info, of_slivers,))
                for s in of_m_info.get("slivers"):
                    ro_manifest.of_sliver(s)

                ro_slivers.extend(of_slivers)
                # introduce slice-monitoring info for SDN resources
                try:
                    slice_monitor.add_sdn_resources(
                        slice_urn, of_m_info.get("slivers"))
                except Exception as e:
                    logger.warning("Delegate could not monitor SDN resources" +
                                   " upon Provision. Details: %s", (e,))

            elif peer.get("type") == self._allowed_peers.get("PEER_TNRM"):
                tn_m_info, tn_slivers = TNUtils().manage_provision(
                    peer, v, credentials, best_effort, end_time, geni_users)

                logger.debug("tn_m=%s, tn_s=%s" % (tn_m_info, tn_slivers,))
                for n in tn_m_info.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in tn_m_info.get("links"):
                    ro_manifest.tn_link(l)

                ro_slivers.extend(tn_slivers)
                # introduce slice-monitoring info for TN resources
                try:
                    slice_monitor.add_tn_resources(
                        slice_urn, tn_m_info.get("nodes"),
                        tn_m_info.get("links"), peer)
                except Exception as e:
                    logger.warning("Delegate could not monitor TN resources" +
                                   " upon Provision. Details: %s", (e,))

            elif peer.get("type") == self._allowed_peers.get("PEER_SERM"):
                se_m_info, se_slivers = SEUtils().manage_provision(
                    peer, v, credentials, best_effort, end_time, geni_users)

                logger.debug("se_m=%s, se_s=%s" % (se_m_info, se_slivers,))
                for n in se_m_info.get("nodes"):
                    ro_manifest.se_node(n)
                for l in se_m_info.get("links"):
                    ro_manifest.se_link(l)

                ro_slivers.extend(se_slivers)
                # introduce slice-monitoring info for SE resources
                try:
                    slice_monitor.add_se_resources(
                        slice_urn, se_m_info.get("nodes"),
                        se_m_info.get("links"))
                except Exception as e:
                    logger.warning("Delegate could not monitor SE resources" +
                                   " upon Provision. Details: %s", (e,))

            elif peer.get("type") == self._allowed_peers.get("PEER_RO"):
                ro_m_info, ro_slivers_ro = ROUtils().manage_provision(
                    peer, v, credentials, best_effort, end_time, geni_users)

                logger.debug("ro_m=%s, ro_s=%s" % (ro_m_info, ro_slivers,))
                ro_manifest = ROUtils.generate_describe_manifest(
                    ro_manifest, ro_m_info)

                ro_slivers.extend(ro_slivers_ro)
                # introduce slice-monitoring info for ALL the resource types!
                try:
                    slice_monitor.add_c_resources(
                        slice_urn, ro_m_info.get("com_nodes"))
                    slice_monitor.add_sdn_resources(
                        slice_urn, ro_m_info.get("sdn_slivers"))
                    slice_monitor.add_tn_resources(
                        slice_urn, ro_m_info.get("tn_nodes"),
                        ro_m_info.get("tn_links"), peer)
                    slice_monitor.add_se_resources(
                        slice_urn, ro_m_info.get("se_nodes"),
                        ro_m_info.get("se_links"))
                except Exception as e:
                    logger.warning("Delegate could not monitor RO resources" +
                                   " upon Provision. Details: %s", (e,))

        # send slice-monitoring info to the monitoring system
        try:
            # Before sending the slice info, we need to add some "virtual"
            # links (island-to-island)!
            slice_monitor.add_island_to_island_links(slice_urn)
            slice_monitor.send()
            # add slice_monitoring object to the slice table
            db_sync_manager.store_slice_monitoring_info(
                slice_urn, slice_monitor.serialize())
        except Exception as e:
            logger.warning("Delegate could not send (store) slice monitoring" +
                           " information upon Provision. Details: %s", (e,))

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))

        # In order to prevent data conversion error, we manipulate the
        # geni-expires parameter. At least 1 parameter should be not null!
        valid_geni_expires = None
        for s in ro_slivers:
            if s["geni_expires"] is not None:
                valid_geni_expires = s["geni_expires"]
                break
        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(
            ro_slivers, valid_geni_expires)
        return ("%s" % ro_manifest, ro_slivers)

    @trace_method_inputs
    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_slivers, last_slice = [], ""

        if self._verify_users:
            for urn in urns:
                logger.debug("status: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") in self._allowed_peers.values():
                last_slice, slivers = CommonUtils().manage_status(
                    peer, v, credentials)

                logger.debug("slivers=%s, urn=%s" % (slivers, last_slice))
                ro_slivers.extend(slivers)

        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(ro_slivers)

        return last_slice, ro_slivers

    @trace_method_inputs
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        """
        Performs a GENI operational action the requested resources, identified
        each by an URN.
        When best_effort is enabled, deletion will be attempted on every
        resource.

        @param urns list of URNs with the identifiers of the resources to
            be treated
        @param client_cert client certificate (X509)
        @param credentials client credential(s), provided by the ClearingHouse
            and generated after the certificates
        @param action name of the GENI action to be processed.
            Typical values are { geni_start, geni_stop, geni_restart }, but
            others may be allowed
        @param best_effort flag to describe the behaviour upon a failure
                * best_effort = True : as much operations as possible are
                                       performed upon an error condition
                * best_effort = False : the set of operations will be stopped
                                        if an error occurs
        @return ro_slivers structure containing information of slivers (URN,
            expiration date, etc)
        """
        ro_slivers = []

        internal_action = self.__translate_action(action)
        logger.info("action=%s, best_effort=%s, internal_action=%s" %
                    (action, best_effort, internal_action,))

        if self._verify_users:
            for urn in urns:
                logger.debug("poa: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials,
                              urn, (internal_action,))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") in self._allowed_peers.values():
                slivers = CommonUtils().manage_operational_action(
                    peer, v, credentials, action, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        ro_slivers = CommonUtils.convert_sliver_dates_to_datetime(ro_slivers)
        return ro_slivers

    @trace_method_inputs
    def delete(self, urns, client_cert, credentials, best_effort):
        """
        Deletes the requested resources, identified each by an URN.
        When best_effort is enabled, deletion will be attempted on every
        resource.

        @param urns list of URNs with the identifiers of the resources to
            be treated
        @param client_cert client certificate (X509)
        @param credentials client credential(s), provided by the ClearingHouse
            and generated after the certificates
        @param best_effort flag to describe the behaviour upon a failure
                * best_effort = True : as much operations as possible are
                                       performed upon an error condition
                * best_effort = False : the set of operations will be stopped
                                        if an error occurs
        @return ro_slivers structure containing information of slivers (URN,
            expiration date, etc)
        """
        ro_slivers = []
        client_urn = None
        if self._verify_users:
            for urn in urns:
                logger.debug("delete: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("deletesliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

        logger.info("best_effort=%s" % (best_effort,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer_by_routing_key(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") in self._allowed_peers.values():
                slivers = CommonUtils().manage_delete(
                    peer, v, credentials, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        db_urns = []
        for s in ro_slivers:
            s["geni_expires"] = dates.rfc3339_to_datetime(s["geni_expires"])
            db_urns.append(s.get("geni_sliver_urn"))
        logger.debug("RO-Slivers(%d)=%s, DB-URNs(%d)=%s" %
                     (len(ro_slivers), ro_slivers, len(db_urns), db_urns))

        # update MS to stop slice-monitoring collection
        slice_urn = db_sync_manager.get_slice_urn(urns)

        if slice_urn:
            try:
                # MS needs to be sent the whole slice data in order to
                # delete it
                slice_monitor = SliceMonitoring()
                slice_monitor.delete_slice_topology(slice_urn)
            except Exception as e:
                logger.warning("Delegate could not send slice monitoring" +
                               " information upon Delete. Details: %s", (e,))
            db_sync_manager.delete_slice_sdn(slice_urn)

        db_sync_manager.delete_slice_urns(db_urns)
        return ro_slivers

    @trace_method_inputs
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        if self._verify_users:
            logger.debug("shutdown: authenticate the user...")
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, slice_urn, ("shutdown",))
            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        logger.info("slice_urn=%s" % (slice_urn,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    # Helpers
    def __insert_slice_info(self, rtype, slice_urn, db_slivers, ro_db_slivers):
        logger.debug("Insert %s slice info: slice_urn=%s, slivers=%s" %
                     (rtype, slice_urn, db_slivers,))
        id_ = db_sync_manager.store_slice_info(slice_urn, db_slivers)
        logger.debug("Stored %s slice info: id=%s" % (rtype, id_,))
        ro_db_slivers.extend(db_slivers)
        logger.debug("RO-DB-Slivers(%d): %s" %
                     (len(ro_db_slivers), ro_db_slivers))

    def __translate_action(self, geni_action):
        actions_to_permissions = {
            self.OPERATIONAL_ACTION_START: "startslice",
            self.OPERATIONAL_ACTION_STOP: "stopslice",
            self.OPERATIONAL_ACTION_RESTART: "updateslice",
            self.OPERATIONAL_ACTION_UPDATE_USERS: "updateslice",
            self.OPERATIONAL_ACTION_UPDATING_USERS_CANCEL: "updateslice",
            self.OPERATIONAL_ACTION_CONSOLE_URL: "getsliceresources",
            self.OPERATIONAL_ACTION_SHARELAN: "updateslice",
            self.OPERATIONAL_ACTION_UNSHARELAN: "updateslice",
        }
        # Look for a mapping within the action-permision dictionary.
        # Otherwise return "unknown"
        return actions_to_permissions.get(geni_action, "unknown")

    def __schedule_slice_release(self, end_time, slivers):
        scheduler = ROSchedulerService.get_scheduler()
        logger.debug("schedule_slice_release: endtime=%s, slivers=%s, obj=%s" %
                     (end_time, slivers, scheduler,))
        if (end_time is not None) and (scheduler is not None):
            urns = [s.get("geni_sliver_urn") for s in slivers]
            ROSchedulerService.get_scheduler().add_job(
                slice_expiration, "date", run_date=end_time, args=[urns])
