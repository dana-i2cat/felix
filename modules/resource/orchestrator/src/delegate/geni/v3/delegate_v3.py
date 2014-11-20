from delegate.geni.v3.base import GENIv3DelegateBase
from delegate.geni.v3.db_manager import db_sync_manager
from delegate.geni.v3.rm_adaptor import AdaptorFactory
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3 import rm_adaptor
from delegate.geni.v3.scheduler.ro_scheduler import ROSchedulerService
from delegate.geni.v3.scheduler.jobs import slice_expiration

from delegate.geni.v3.rspecs.commons import validate
from delegate.geni.v3.rspecs.commons_of import Match
from delegate.geni.v3.rspecs.commons_tn import Node, Interface
from delegate.geni.v3.rspecs.commons_se import SELink
from delegate.geni.v3.rspecs.ro.advertisement_formatter import\
    ROAdvertisementFormatter
from delegate.geni.v3.rspecs.ro.request_parser import RORequestParser
from delegate.geni.v3.rspecs.ro.manifest_formatter import ROManifestFormatter
from delegate.geni.v3.rspecs.openflow.request_formatter import\
    OFv3RequestFormatter
from delegate.geni.v3.rspecs.tnrm.request_formatter import\
    TNRMv3RequestFormatter
from delegate.geni.v3.rspecs.serm.request_formatter import\
    SERMv3RequestFormatter
from delegate.geni.v3.rspecs.crm.manifest_parser import CRMv3ManifestParser
from delegate.geni.v3.rspecs.openflow.manifest_parser import OFv3ManifestParser
from delegate.geni.v3.rspecs.tnrm.manifest_parser import TNRMv3ManifestParser
from delegate.geni.v3.rspecs.serm.manifest_parser import SERMv3ManifestParser

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
        from lxml import etree
        client_urn, client_uuid, client_email =\
            self.auth(client_cert, credentials, None, ("listslices",))

        logger.info("Client urn=%s, uuid=%s, email=%s" % (
            client_urn, client_uuid, client_email,))
        logger.info("geni_available=%s", geni_available)

        sl = "http://www.geni.net/resources/rspec/3/ad.xsd"
        rspec = ROAdvertisementFormatter(schema_location=sl)
        
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

                ro_manifest.of_sliver(of_m_info.get("description"),
                                      of_m_info.get("ref"),
                                      of_m_info.get("email"))
                ro_slivers.extend(of_slivers)

            elif peer.get("type") == "transport_network":
                tn_m_info, last_slice, tn_slivers =\
                    self.__manage_tn_describe(peer, v, credentials)

                logger.debug("tn_m=%s, tn_s=%s, urn=%s" %
                             (tn_m_info, tn_slivers, last_slice))
                for n in tn_m_info.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in tn_m_info.get("links"):
                    ro_manifest.tn_link(l)

                ro_slivers.extend(tn_slivers)

            elif peer.get("type") == "stitching_entity":
                se_m_info, last_slice, se_slivers =\
                    self.__manage_se_describe(peer, v, credentials)

                logger.debug("se_m=%s, se_s=%s, urn=%s" %
                             (se_m_info, se_slivers, last_slice))
                for n in se_m_info.get("nodes"):
                    ro_manifest.se_node(n)
                for l in se_m_info.get("links"):
                    ro_manifest.se_link(l)

                ro_slivers.extend(se_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))

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

        # COM resources
        se_com_info = None
        slivers = req_rspec.com_slivers()
        logger.debug("\n\n\n\n\n\n\n\n\n\n\n\n\n COM slivers=%s", slivers)
        if len(slivers) > 0:
            logger.debug("Found a COM-slivers segment (%d): %s" %
                         (len(slivers), slivers,))
            (com_m_info, com_slivers, db_slivers) =\
                self.__manage_com_allocate(slice_urn, credentials, end_time,
                                          slivers, req_rspec)
            logger.debug("com_m=%s, com_s=%s, com_s=%s" %
                         (com_m_info, com_slivers, db_slivers))
            for m in com_m_info:
                for s in m.get("slivers"):
                    ro_manifest.com_sliver(s)
            ro_slivers.extend(com_slivers)
            ro_db_slivers.extend(db_slivers)

        # OF resources
        se_sdn_info = None
        sliver = req_rspec.of_sliver()
        if sliver is not None:
            logger.debug("Found an OF-sliver segment: %s", sliver)
            (of_m_info, of_slivers, db_slivers, se_sdn_info) =\
                self.__manage_sdn_allocate(slice_urn, credentials, end_time,
                                           sliver, req_rspec)

            logger.debug("of_m=%s, of_s=%s, db_s=%s" %
                         (of_m_info, of_slivers, db_slivers))
            for m in of_m_info:
                ro_manifest.of_sliver(m.get("description"),
                                      m.get("ref"),
                                      m.get("email"))
            ro_slivers.extend(of_slivers)
            ro_db_slivers.extend(db_slivers)

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
                self.__manage_tn_allocate(slice_urn, credentials, end_time,
                                          nodes, links)

            logger.debug("tn_m=%s, tn_s=%s, db_s=%s" %
                         (tn_m_info, tn_slivers, db_slivers))
            for m in tn_m_info:
                for n in m.get("nodes"):
                    ro_manifest.tn_node(n)
                for l in m.get("links"):
                    ro_manifest.tn_link(l)

            ro_slivers.extend(tn_slivers)
            ro_db_slivers.extend(db_slivers)

        # SE resources
        if (se_sdn_info is not None) and (len(se_sdn_info) > 0) and\
           (se_sdn_info is not None) and (len(se_tn_info) > 0):
            logger.debug("Found a SE-sdn segment (%d): %s" %
                         (len(se_sdn_info), se_sdn_info,))
            logger.debug("Found a SE-tn segment (%d): %s" %
                         (len(se_tn_info), se_tn_info,))
            (se_m_info, se_slivers, db_slivers) =\
                self.__manage_se_allocate(slice_urn, credentials, end_time,
                                          se_sdn_info, se_tn_info)
            logger.debug("se_m=%s, se_s=%s, db_s=%s" %
                         (se_m_info, se_slivers, db_slivers))
            for m in se_m_info:
                for n in m.get("nodes"):
                    ro_manifest.se_node(n)
                for l in m.get("links"):
                    ro_manifest.se_link(l)

            ro_slivers.extend(se_slivers)
            ro_db_slivers.extend(db_slivers)

        logger.debug("RO-ManifestFormatter=%s" % (ro_manifest,))

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))

        logger.debug("RO-DB-Slivers(%d)=%s" %
                     (len(ro_db_slivers), ro_db_slivers,))
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

        etime_str = self.__datetime2str(expiration_time)
        for r, v in route.iteritems():
            peer = db_sync_manager.get_configured_peer(r)
            logger.debug("peer=%s" % (peer,))
            if peer.get("type") in ["sdn_networking", "transport_network",
                                    "stitching_entity"]:
                slivers = self.__manage_renew(
                    peer, v, credentials, etime_str, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))
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
            if peer.get("type") in ["sdn_networking", "transport_network",
                                    "stitching_entity"]:
                lastslice, slivers = self.__manage_status(peer, v, credentials)

                logger.debug("slivers=%s, urn=%s" % (slivers, lastslice))
                ro_slivers.extend(slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))
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
            if peer.get("type") in ["sdn_networking", "transport_network",
                                    "stitching_entity"]:
                slivers = self.__manage_operational_action(
                    peer, v, credentials, action, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        logger.debug("RO-Slivers(%d)=%s" % (len(ro_slivers), ro_slivers,))
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
            if peer.get("type") in ["sdn_networking", "transport_network",
                                    "stitching_entity"]:
                slivers = self.__manage_delete(
                    peer, v, credentials, best_effort)

                logger.debug("slivers=%s" % (slivers,))
                ro_slivers.extend(slivers)

        db_urns = []
        for s in ro_slivers:
            s["geni_expires"] = self.__str2datetime(s["geni_expires"])
            db_urns.append(s.get("geni_sliver_urn"))
        logger.debug("RO-Slivers(%d)=%s, DB-URNs(%d)=%s" %
                     (len(ro_slivers), ro_slivers, len(db_urns), db_urns))

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
        logger.debug("Adaptor=%s" % (adaptor,))
        return adaptor.allocate(slice_urn, credentials[0]["geni_value"],
                                "%s" % req_rspec, end_time)

    def __extend_slivers(self, values, routing_key, slivers, db_slivers):
        logger.info("Slivers=%s" % (values,))
        slivers.extend(values)
        for dbs in values:
            db_slivers.append({"geni_sliver_urn": dbs.get("geni_sliver_urn"),
                               "routing_key": routing_key})

    def __extract_se_from_sdn(self, groups, matches):
        ret = []
        for m in matches:
            vlan_id = m.get('packet').get('dl_vlan')
            if vlan_id is None:
                continue

            dpids = []
            for mg in m.get('use_groups'):
                for g in groups:
                    if g.get('name') == mg.get('name'):
                        for gds in g.get('dpids'):
                            dpids.append(gds.get('component_id'))

            for mds in m.get('dpids'):
                dpids.append(mds.get('component_id'))

            if len(dpids) > 0:
                ret.append({'vlan': vlan_id, 'dpids': dpids})

        return ret

    def __manage_com_allocate(self, slice_urn, credentials, slice_expiration, sliver, parser):
        # TODO CHECK THAT IT WORKS
        route = {}
        slivers = parser.com_slivers()
        logger.debug("Slivers=%s" % (slivers,))

        #m = """<rspec type="manifest" xmlns="http://www.geni.net/resources/rspec/3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/manifest.xsd">  
#  <node client_id="None" component_id="urn:publicid:IDN+ocf:i2cat:vtam+node+Verdaguer" component_manager_id="urn:publicid:IDN+ocf:i2cat:vtam+authority+cm" sliver_id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+sliver+692550">
#</node>  
#</rspec>"""
#        manifest = CRMv3ManifestParser(from_string=m)
#        print "manifest >>>>>>>>>>", manifest
#        slivers = manifest.sliver()
#        print "slivers >>>>>>>>>>", slivers

        for sliver in slivers:
            route.update(sliver)

        logger.info("Route=%s" % (route,))
        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            (m, ss) = self.__send_request_rspec(k, v, slice_urn, credentials, slice_expiration)
            logger.debug("delegate > manifest: %s" % str(m))
            manifest = COMv3ManifestParser(from_string=m)
            logger.debug("COMv3ManifestParser=%s" % (manifest,))

            sliver = manifest.sliver()
            logger.info("Sliver=%s" % (sliver,))
            manifests.append(sliver)

            self.__extend_slivers(ss, k, slivers, db_slivers)

        return (manifests, slivers, db_slivers)

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

        se_sdn_info = self.__extract_se_from_sdn(groups, matches)
        logger.debug("SE-SDN-INFO=%s" % (se_sdn_info,))

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

        return (manifests, slivers, db_slivers, se_sdn_info)

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

    def __extract_se_from_tn(self, nodes, links):
        ret, ifref = [], set()
        for l in links:
            for p in l.get('property'):
                ifref.add(p.get('source_id'))
                ifref.add(p.get('dest_id'))

        for n in nodes:
            for i in n.get('interfaces'):
                if i.get('component_id') in ifref:
                    for v in i.get('vlan'):
                        ret.append({'vlan': v.get('tag'),
                                    'interface': i.get('component_id')})

        return ret

    def __manage_tn_allocate(self, surn, creds, end, nodes, links):
        route = {}
        self.__update_tn_node_route(route, nodes)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        self.__update_tn_link_route(route, links)
        logger.debug("Links(%d)=%s" % (len(links), links,))

        self.__update_tn_route_rspec(route, nodes, links)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers, se_tn_info = [], [], [], []

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

            se_tn = self.__extract_se_from_tn(nodes, links)
            logger.debug("SE-TN-INFO=%s" % (se_tn,))
            if len(se_tn) > 0:
                se_tn_info.extend(se_tn)

        return (manifests, slivers, db_slivers, se_tn_info)

    def __update_se_info_route(self, route, values, key):
        for v in values:
            k, ifs = db_sync_manager.get_se_link_routing_key(v.get(key))
            v['routing_key'] = k
            v['internal_ifs'] = ifs
            node = db_sync_manager.get_se_node_info(k)
            v['node'] = node
            if (k is not None) and (k not in route):
                sl = "http://www.geni.net/resources/rspec/3/request.xsd"
                route[k] = SERMv3RequestFormatter(schema_location=sl)

    def __update_se_nodes(self, nodes, values):
        for v in values:
            if v.get('node') is not None:
                cid = v.get('node').get('component_id')
                cmid = v.get('node').get('component_manager_id')
                if len(nodes) > 0:
                    for i in nodes:
                        if (i.serialize().get('component_id') != cid) and\
                           (i.serialize().get('component_manager_id') != cmid):
                            n = Node(cid, cmid,
                                     sliver_type_name=v.get('routing_key'))
                            nodes.append(n)
                else:
                    n = Node(cid, cmid, sliver_type_name=v.get('routing_key'))
                    nodes.append(n)

        for v in values:
            if v.get('node') is not None:
                for n in nodes:
                    scid = v.get('node').get('component_id')
                    scmid = v.get('node').get('component_manager_id')
                    ncid = n.serialize().get('component_id')
                    ncmid = n.serialize().get('component_manager_id')
                    if (scid == ncid) and (scmid == ncmid):
                        for i in v.get('internal_ifs'):
                            intf = Interface(i.get('component_id'))
                            intf.add_vlan(v.get('vlan'), "")
                            n.add_interface(intf.serialize())

    def __create_selink(self, if1, if2, sliver_id):
        i = if1.rindex(':')
        n1, name1 = if1[0:i], if1[i+1:len(if1)]
        i = if2.rindex(':')
        n2, name2 = if2[0:i], if2[i+1:len(if1)]

        if n1 != n2:
            raise Exception("SELink: differs node cid (%s,%s)" % (n1, n2))

        cid = n1 + ':' + name1 + '-' + name2
        typee, cm_name = db_sync_manager.get_se_link_info(n1)

        l = SELink(cid, typee, cm_name, sliver=sliver_id)
        l.add_interface_ref(if1)
        l.add_interface_ref(if2)
        return l

    def __update_se_link(self, links, svalues, tvalues):
        for s in svalues:
            for sintf in s.get('internal_ifs'):
                for t in tvalues:
                    for tintf in t.get('internal_ifs'):
                        if s.get('routing_key') == t.get('routing_key'):
                            l = self.__create_selink(sintf.get('component_id'),
                                                     tintf.get('component_id'),
                                                     s.get('routing_key'))
                            links.append(l)

    def __extract_se_info(self, sdn, tn):
        nodes, links = [], []
        self.__update_se_nodes(nodes, sdn)
        self.__update_se_nodes(nodes, tn)
        self.__update_se_link(links, sdn, tn)

        return [n.serialize() for n in nodes], [l.serialize() for l in links]

    def __update_se_route_rspec(self, route, sdn_info, tn_info):
        nodes, links = self.__extract_se_info(sdn_info, tn_info)
        logger.debug("SE-Nodes=%s" % (nodes,))
        logger.debug("SE-Links=%s" % (links,))

        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("sliver_type_name") == key:
                    n["sliver_type_name"] = None
                    rspec.node(n)
            for l in links:
                if l.get("sliver_id") == key:
                    l["sliver"] = None
                    rspec.link(l)

    def __manage_se_allocate(self, surn, creds, end, sdn_info, tn_info):
        route = {}
        self.__update_se_info_route(route, sdn_info, 'dpids')
        logger.debug("SE-SdnInfo(%d)=%s" % (len(sdn_info), sdn_info,))
        self.__update_se_info_route(route, tn_info, 'interface')
        logger.debug("SE-TnInfo(%d)=%s" % (len(tn_info), tn_info,))

        self.__update_se_route_rspec(route, sdn_info, tn_info)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
            manifest = SERMv3ManifestParser(from_string=m)
            logger.debug("SERMv3ManifestParser=%s" % (manifest,))
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
        # self.__validate_rspec(manifest.get_rspec())

        sliver = manifest.sliver()
        logger.info("Sliver=%s" % (sliver,))

        return (sliver, urn, ss)

    def __manage_tn_describe(self, peer, urns, creds):
        adaptor = AdaptorFactory.create_from_db(peer)
        m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

        manifest = TNRMv3ManifestParser(from_string=m)
        logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
        self.__validate_rspec(manifest.get_rspec())

        nodes = manifest.nodes()
        logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
        links = manifest.links()
        logger.info("Links(%d)=%s" % (len(links), links,))

        return ({"nodes": nodes, "links": links}, urn, ss)

    def __manage_se_describe(self, peer, urns, creds):
        adaptor = AdaptorFactory.create_from_db(peer)
        m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

        manifest = SERMv3ManifestParser(from_string=m)
        logger.debug("SERMv3ManifestParser=%s" % (manifest,))
        self.__validate_rspec(manifest.get_rspec())

        nodes = manifest.nodes()
        logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
        links = manifest.links()
        logger.info("Links(%d)=%s" % (len(links), links,))

        return ({"nodes": nodes, "links": links}, urn, ss)

    def __manage_status(self, peer, urns, creds):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.status(urns, creds[0]["geni_value"])

    def __manage_renew(self, peer, urns, creds, etime, beffort):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.renew(urns, creds[0]["geni_value"], etime, beffort)

    def __manage_operational_action(self, peer, urns, creds, action, beffort):
        adaptor = AdaptorFactory.create_from_db(peer)
        return adaptor.perform_operational_action(
            urns, creds[0]["geni_value"], action, beffort)

    def __manage_delete(self, peer, urns, creds, beffort):
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
