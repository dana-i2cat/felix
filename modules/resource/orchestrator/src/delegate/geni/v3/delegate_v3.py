from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor
from delegate.geni.v3.scheduler.ro_scheduler import ROSchedulerService
from delegate.geni.v3.scheduler.jobs import slice_expiration

from delegate.geni.v3.rspecs.commons import validate
from delegate.geni.v3.rspecs.commons_of import Match
from delegate.geni.v3.rspecs.ro.advertisement_formatter import\
    ROAdvertisementFormatter
from delegate.geni.v3.rspecs.ro.request_parser import RORequestParser
from delegate.geni.v3.rspecs.ro.manifest_formatter import ROManifestFormatter
from delegate.geni.v3.rspecs.openflow.request_formatter import\
    OFv3RequestFormatter
from delegate.geni.v3.rspecs.tnrm.request_formatter import\
    TNRMv3RequestFormatter
from delegate.geni.v3.rspecs.openflow.manifest_parser import OFv3ManifestParser
from delegate.geni.v3.rspecs.tnrm.manifest_parser import TNRMv3ManifestParser

from dateutil import parser as dateparser

import core
logger = core.log.getLogger("geniv3delegate")


class GENIv3Delegate(GENIv3DelegateBase):
    """
    """
    # TODO should also include a changing component, identified by a config key
    URN_PREFIX = "urn:RO"

    def __init__(self):
        super(GENIv3Delegate, self).__init__()
        self._resource_manager = rm_adaptor

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

    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug("list_resources: authenticate the user...")
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, None, ("listslices",))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("geni_available=%s", geni_available)

        sl = "http://www.geni.net/resources/rspec/3/ad.xsd"
        rspec = ROAdvertisementFormatter(schema_location=sl)
        logger.debug("\n\n\n\n\n[REMOVE] DELEGATE.list_resources\n\n\n\n\n")
        try:
            logger.debug("COM resources: nodes")
            for n in db_sync_manager.get_com_nodes():
                rspec.com_node(n)
            
            logger.debug("OF resources: datapaths")
            for d in db_sync_manager.get_sdn_datapaths():
                rspec.datapath(d)

            logger.debug("TN resources: nodes")
            for n in db_sync_manager.get_tn_nodes():
                rspec.tn_node(n)
            
            logger.debug("COM resources: com-links")
            for l in db_sync_manager.get_com_links():
                logger.error("COM-LINK=%s" % l)
                rspec.com_link(l)
            
            logger.debug("OF resources: of-links & fed-links")
            (of_links, fed_links) = db_sync_manager.get_sdn_links()
            for l in of_links:
                rspec.of_link(l)

            for l in fed_links:
                rspec.fed_link(l)

            logger.debug("TN resources: tn-links")
            for l in db_sync_manager.get_tn_links():
                logger.error("TN-LINK=%s" % l)
                rspec.tn_link(l)

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
            logger.debug("describe: authenticate the user for %s" % (urn))
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urn, ("sliverstatus",))

            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == "sdn_networking":
                of_m_info, last_slice, of_slivers =\
                    self.__manage_sdn_describe(peer, v, credentials)

                logger.debug("of_m=%s, of_s=%s, urn=%s" %
                             (of_m_info, of_slivers, last_slice))

                ro_manifest.sliver(of_m_info.get("description"),
                                   of_m_info.get("ref"),
                                   of_m_info.get("email"))
                ro_slivers.extend(of_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))
        logger.debug("RO-Slivers=%s" % (ro_slivers,))

        return {"geni_rspec": "%s" % ro_manifest,
                "geni_urn": last_slice,
                "geni_slivers": ro_slivers}

    def allocate(self, slice_urn, client_cert, credentials,
                 rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug("allocate: authenticate the user...")
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, slice_urn, ("createsliver",))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("slice_urn=%s, end_time=%s, rspec=%s" % (
            slice_urn, end_time, rspec,))

        req_rspec = RORequestParser(from_string=rspec)
        self.__validate_rspec(req_rspec.get_rspec())

        ro_manifest, ro_slivers, ro_db_slivers = ROManifestFormatter(), [], []
        # OF resources
        sliver = req_rspec.of_sliver()
        if sliver is not None:
            logger.debug("Found an OF-sliver segment: %s", sliver)
            (of_m_info, of_slivers, db_slivers) = self.__manage_sdn_allocate(
                slice_urn, credentials, end_time, sliver, req_rspec)

            logger.debug("of_m=%s, of_s=%s, db_s=%s" %
                         (of_m_info, of_slivers, db_slivers))
            for m in of_m_info:
                ro_manifest.of_sliver(m.get("description"),
                                      m.get("ref"),
                                      m.get("email"))
            ro_slivers.extend(of_slivers)
            ro_db_slivers.extend(db_slivers)

        # TN resources
        nodes = req_rspec.tn_nodes()
        links = req_rspec.tn_links()
        if (len(nodes) > 0) or (len(links) > 0):
            logger.debug("Found a TN-nodes segment (%d): %s" %
                         (len(nodes), nodes,))
            logger.debug("Found a TN-links segment (%d): %s" %
                         (len(links), links,))
            (tn_m_info, tn_slivers, db_slivers) = self.__manage_tn_allocate(
                slice_urn, credentials, end_time, nodes, links)

            logger.debug("tn_m=%s, tn_s=%s, db_s=%s" %
                         (tn_m_info, tn_slivers, db_slivers))
            for m in tn_m_info:
                for n in m.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in m.get("links"):
                    ro_manifest.tn_link(l)

            ro_slivers.extend(tn_slivers)
            ro_db_slivers.extend(db_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))

        logger.debug("RO-DB-Slivers=%s" % (ro_db_slivers,))
        id_ = db_sync_manager.store_slice_info(slice_urn, ro_db_slivers)

        logger.info("allocate successfully completed: %s", id_)
        self.__schedule_slice_release(end_time, ro_db_slivers)
        return ("%s" % ro_manifest, ro_slivers)

    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_slivers = []

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

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == "sdn_networking":
                etime_str = self.__datetime2str(expiration_time)
                of_slivers = self.__manage_sdn_renew(
                    peer, v, credentials, etime_str, best_effort)

                logger.debug("of_s=%s" % (of_slivers,))
                ro_slivers.extend(of_slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))
        return ro_slivers

    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        logger.debug("provision: authenticate the user...")
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, urns, ("renewsliver",))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("urns=%s, best_effort=%s, end_time=%s, geni_users=%s" % (
            urns, best_effort, end_time, geni_users,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_slivers, last_slice = [], ""

        for urn in urns:
            logger.debug("status: authenticate the user for %s" % (urn))
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urn, ("sliverstatus",))

            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == "sdn_networking":
                last_slice, of_slivers =\
                    self.__manage_sdn_status(peer, v, credentials)

                logger.debug("of_s=%s, urn=%s" % (of_slivers, last_slice))
                ro_slivers.extend(of_slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))
        return last_slice, ro_slivers

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        ro_slivers = []

        internal_action = self.__translate_action(action)
        logger.info("action=%s, best_effort=%s, internal_action=%s" %
                    (action, best_effort, internal_action,))

        for urn in urns:
            logger.debug("poa: authenticate the user for %s" % (urn))
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, urn, (internal_action,))

            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        route = db_sync_manager.get_slice_routing_keys(urns)
        logger.debug("Route=%s" % (route,))

        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == "sdn_networking":
                of_slivers = self.__manage_sdn_operational_action(
                    peer, v, credentials, action, best_effort)

                logger.debug("of_s=%s" % (of_slivers,))
                ro_slivers.extend(of_slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers=%s" % (ro_slivers,))
        return ro_slivers

    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        ro_slivers = []

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
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") == "sdn_networking":
                of_slivers = self.__manage_sdn_delete(
                    peer, v, credentials, best_effort)

                logger.debug("of_s=%s" % (of_slivers,))
                ro_slivers.extend(of_slivers)

        db_urns = []
        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
            db_urns.append(s.get("geni_sliver_urn"))
        logger.debug("RO-Slivers=%s, DB-URNs=%s" % (ro_slivers, db_urns))

        db_sync_manager.delete_slice_urns(db_urns)
        return ro_slivers

    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.debug("shutdown: authenticate the user...")
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, slice_urn, ("shutdown",))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("slice_urn=%s" % (slice_urn,))
        raise geni_ex.GENIv3GeneralError("Not implemented yet!")

    def __update_sdn_route(self, route, values):
        for v in values:
            for dpid in v.get("dpids"):
                k = db_sync_manager.get_sdn_datapath_routing_key(dpid)
                dpid["routing_key"] = k
                if k not in route:
                    sl = "http://www.geni.net/resources/rspec/3/request.xsd"
                    route[k] = OFv3RequestFormatter(schema_location=sl)

    def __update_sdn_route_rspec(self, route, sliver, controllers,
                                 groups, matches):
        for key, rspec in route.iteritems():
            rspec.sliver(sliver.get("description"),
                         sliver.get("ref"),
                         sliver.get("email"))
            for c in controllers:
                rspec.controller(c.get("url"), c.get("type"))
            for g in groups:
                rspec.group(g.get("name"))
                for dpid in g.get("dpids"):
                    if dpid.get("routing_key") == key:
                        rspec.group_datapath(g.get("name"), dpid)
            for m in matches:
                match = Match()
                for uf in m.get("use_groups"):
                    match.add_use_group(uf.get("name"))
                for dpid in m.get("dpids"):
                    if dpid.get("routing_key") == key:
                        match.add_datapath(dpid)
                match.set_packet(m.get("packet").get("dl_src"),
                                 m.get("packet").get("dl_dst"),
                                 m.get("packet").get("dl_type"),
                                 m.get("packet").get("dl_vlan"),
                                 m.get("packet").get("nw_src"),
                                 m.get("packet").get("nw_dst"),
                                 m.get("packet").get("nw_proto"),
                                 m.get("packet").get("tp_src"),
                                 m.get("packet").get("tp_dst"))
                rspec.match(match.serialize())

    def __send_request_rspec(self, routing_key, req_rspec, slice_urn,
                             credentials, end_time):
        peer = db_sync_manager.get_configured_peer(routing_key)
        logger.debug("Peer=%s" % (peer,))
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.allocate(slice_urn, credentials[0]["geni_value"],
                                "%s" % req_rspec, end_time)

    def __extend_slivers(self, values, routing_key, slivers, db_slivers):
        logger.info("Slivers=%s" % (values,))
        slivers.extend(values)
        for dbs in values:
            db_slivers.append({"geni_sliver_urn": dbs.get("geni_sliver_urn"),
                               "routing_key": routing_key})

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
            (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
            manifest = OFv3ManifestParser(from_string=m)
            logger.debug("OFv3ManifestParser=%s" % (manifest,))

            sliver = manifest.sliver()
            logger.info("Sliver=%s" % (sliver,))
            manifests.append(sliver)

            self.__extend_slivers(ss, k, slivers, db_slivers)

        return (manifests, slivers, db_slivers)

    def __update_tn_node_route(self, route, values):
        for v in values:
            k = db_sync_manager.get_tn_node_routing_key(v.get("component_id"))
            v["routing_key"] = k
            if k not in route:
                sl = "http://www.geni.net/resources/rspec/3/request.xsd"
                route[k] = TNRMv3RequestFormatter(schema_location=sl)

    def __update_tn_link_route(self, route, values):
        for v in values:
            k = db_sync_manager.get_tn_link_routing_key(
                v.get("component_id"), v.get("component_manager_name"),
                [i.get("component_id") for i in v.get("interface_ref")])
            v["routing_key"] = k
            if k not in route:
                sl = "http://www.geni.net/resources/rspec/3/request.xsd"
                route[k] = TNRMv3RequestFormatter(schema_location=sl)

    def __update_tn_route_rspec(self, route, nodes, links):
        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("routing_key") == key:
                    rspec.node(n)
            for l in links:
                if l.get("routing_key") == key:
                    rspec.link(l)

    def __manage_tn_allocate(self, surn, creds, end, nodes, links):
        route = {}
        self.__update_tn_node_route(route, nodes)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        self.__update_tn_link_route(route, links)
        logger.debug("Links(%d)=%s" % (len(links), links,))

        self.__update_tn_route_rspec(route, nodes, links)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
            manifest = TNRMv3ManifestParser(from_string=m)
            logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
            self.__validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            manifests.append({"nodes": nodes, "links": links})

            self.__extend_slivers(ss, k, slivers, db_slivers)

        return (manifests, slivers, db_slivers)

    def __manage_sdn_describe(self, peer, urns, creds):
        adaptor = AdaptorFactory.create_from_db(peer)
        m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])
        manifest = OFv3ManifestParser(from_string=m)
        logger.debug("OFv3ManifestParser=%s" % (manifest,))

        sliver = manifest.sliver()
        logger.info("Sliver=%s" % (sliver,))

        return (sliver, urn, ss)

    def __manage_sdn_status(self, peer, urns, creds):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.status(urns, creds[0]["geni_value"])

    def __manage_sdn_renew(self, peer, urns, creds, etime, beffort):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.renew(urns, creds[0]["geni_value"], etime, beffort)

    def __manage_sdn_operational_action(self, peer, urns, creds,
                                        action, beffort):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.perform_operational_action(
            urns, creds[0]["geni_value"], action, beffort)

    def __manage_sdn_delete(self, peer, urns, creds, beffort):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.delete(urns, creds[0]["geni_value"], beffort)

    def __validate_rspec(self, generic_rspec):
        (result, error) = validate(generic_rspec)
        if result is not True:
            raise geni_ex.GENIv3GeneralError("RSpec validation failure: %s" % (
                                             error,))
        logger.info("Validation success!")

    def __datetime2str(self, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S.%fZ")

    def __str2datetime(self, strval):
        result = dateparser.parse(strval)
        if result:
            result = result - result.utcoffset()
            result = result.replace(tzinfo=None)
        return result

    def __translate_action(self, geni_action):
        if geni_action == self.OPERATIONAL_ACTION_STOP:
            return "stopslice"
        elif geni_action == self.OPERATIONAL_ACTION_START:
            return "startslice"
        return "unknown"

    def __schedule_slice_release(self, end_time, slivers):
        scheduler = ROSchedulerService.get_scheduler()
        logger.debug("schedule_slice_release: endtime=%s, slivers=%s, obj=%s" %
                     (end_time, slivers, scheduler,))
        if (end_time is not None) and (scheduler is not None):
            urns = [s.get("geni_sliver_urn") for s in slivers]
            ROSchedulerService.get_scheduler().add_job(
                slice_expiration, "date", run_date=end_time, args=[urns])

    # Helper methods
    def _get_sliver_status_hash(self, lease, include_allocation_status=False,
                                include_operational_status=False,
                                error_message=None):
        """Helper method to create the sliver_status return
        values of allocate and other calls."""
        result = {"geni_sliver_urn": self._ip_to_urn(str(lease["ip_str"])),
                  "geni_expires": lease["end_time"],
                  "geni_allocation_status": self.ALLOCATION_STATE_ALLOCATED}

        result["geni_allocation_status"] = self.ALLOCATION_STATE_UNALLOCATED\
            if lease["available"] else self.ALLOCATION_STATE_PROVISIONED

        # there is no state to an ip, so we always return ready
        if (include_operational_status):
            result["geni_operational_status"] = self.OPERATIONAL_STATE_READY

        if (error_message):
            result["geni_error"] = error_message

        return result

    def _get_manifest_rspec(self, leases):
        E = self.lxml_manifest_element_maker("resource-orchestrator")
        manifest = self.lxml_manifest_root()
        for lease in leases:
            # assemble manifest
            r = E.resource()
            r.append(E.ip(lease["ip_str"]))
            # TODO add more info here
        logger.debug("manifest=%s", (manifest,))
