from dateutil import parser as dateparser
from delegate.geni.v3.base import GENIv3DelegateBase

from se_scheduler import SESchedulerService
from delegate.geni.v3.rspecs.commons import validate
from delegate.geni.v3.rspecs.serm.advertisement_formatter import\
    SERMv3AdvertisementFormatter
from delegate.geni.v3.rspecs.serm.advertisement_parser import\
    SERMv3AdvertisementParser

from delegate.geni.v3.rspecs.serm.manifest_formatter import SERMv3ManifestFormatter
from delegate.geni.v3.rspecs.serm.request_parser import SERMv3RequestParser
from delegate.geni.v3.rspecs.serm.request_formatter import\
    SERMv3RequestFormatter
from handler.geni.v3 import exceptions as geni_ex

from core.config import ConfParser
import ast
import core
import se_configurator as SEConfigurator
from se_slices import seSlicesWithSlivers

import ryu_rest_of as se_provision


# TODO: Delete if no error occurs
#from delegate.geni.v3.db_manager import db_sync_manager
# from delegate.geni.v3.rm_adaptor import AdaptorFactory
# Following import cannot be ordered properly
# from delegate.geni.v3 import rm_adaptor
#from scheduler.jobs import slice_expiration
#from scheduler.ro_scheduler import ROSchedulerService
# from delegate.geni.v3.rspecs.commons_of import Match
# from delegate.geni.v3.rspecs.commons_tn import Node, Interface
# from delegate.geni.v3.rspecs.commons_se import SELink
# from delegate.geni.v3.rspecs.crm.manifest_parser import CRMv3ManifestParser
# from delegate.geni.v3.rspecs.crm.request_formatter import CRMv3RequestFormatter
# from delegate.geni.v3.rspecs.openflow.request_formatter import\
#     OFv3RequestFormatter
# from delegate.geni.v3.rspecs.ro.advertisement_formatter import\
#     ROAdvertisementFormatter
# from delegate.geni.v3.rspecs.serm.advertisement_parser import\
#     SERMv3AdvertisementParser
# from delegate.geni.v3.rspecs.ro.manifest_formatter import ROManifestFormatter
# from delegate.geni.v3.rspecs.ro.request_parser import RORequestParser
# from delegate.geni.v3.rspecs.openflow.manifest_parser import OFv3ManifestParser
# from delegate.geni.v3.rspecs.serm.request_formatter import\
#     SERMv3RequestFormatter
# from delegate.geni.v3.rspecs.tnrm.manifest_parser import TNRMv3ManifestParser
# from delegate.geni.v3.rspecs.tnrm.request_formatter import\
#     TNRMv3RequestFormatter

#from apport.fileutils import links_with_shared_library
from datetime import datetime, timedelta
from delegate.geni.v3.se_scheduler import SESchedulerService


logger = core.log.getLogger("geniv3delegate")

test_links_db = {}
link_additional_info={}

RFC3339_FORMAT_STRING = "%Y-%m-%d %H:%M:%S.%fZ"

def se_job_release_resources(time, ports, slice_urn):

    SEResources = SEConfigurator.seConfigurator()
    SESlices = seSlicesWithSlivers()

    print('Release! This was scheduled at %s Resources: %s Slice URN: %s' % (time, ports, slice_urn))

    # Mark resources as free
    SEResources.free_resource_reservation(ports)

    # Remove reservation - TODO
    # SESlices.remove_link_db(slice_urn)

class GENIv3Delegate(GENIv3DelegateBase):
    """
    """

    
    def __init__(self):
        super(GENIv3Delegate, self).__init__()
        # self._resource_manager = rm_adaptor
        self.SEResources = SEConfigurator.seConfigurator()
        self.SESlices = seSlicesWithSlivers()
        self._verify_users =\
            ast.literal_eval(ConfParser("geniv3.conf").get("certificates").get("verify_users"))        

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"stitching-element":
                "http://example.com/stitching-element"}  # /request.xsd

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"stitching-element":
                "http://example.com/stitching-element"}  # /manifest.xsd

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {"stitching-element":
                "http://example.com/stitching-element"}  # /ad.xsd

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
        if self._verify_users:
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, None, ("listslices",))
            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))
        logger.info("geni_available=%s", geni_available)

        sl = "http://www.geni.net/resources/rspec/3/ad.xsd"
        print "listresources invoked"
        rspec = SERMv3AdvertisementFormatter(schema_location=sl)

        links = self.SEResources.get_links_dict_for_rspec()
        nodes = self.SEResources.get_nodes_dict_for_rspec()

        try:
             #links = rspec_string.links()
             print "ALL LINKS: ", links
             #nodes = rspec_string.nodes()
             print "ALL NODES: ", nodes
             logger.debug("SE resources: se-links")
             for l in links:
                 logger.error("SE-LINK=%s" % l)
                 print "link se",l
                 rspec.link(l)
             logger.debug("SE resources: se-node")
             for n in nodes:
                 logger.error("SE-NODE=%s" % n)
                 print "node se",n
                 rspec.node(n)
        except Exception as e:
             raise geni_ex.GENIv3GeneralError(str(e))

        logger.debug("SEAdvertisementFormatter=%s" % (rspec,))
        self.__validate_rspec(rspec.get_rspec())
        return "%s" % rspec

    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        se_manifest, se_slivers, last_slice = SERMv3ManifestFormatter(), [], ""

        result = []

        if self._verify_users:
            for urn in urns:
                logger.debug("describe: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)
            self.SESlices._create_manifest_from_req_n_and_l(se_manifest, nodes,links)

            result.append( 
                            {   
                                "geni_sliver_urn": links_db['geni_sliver_urn'][0].keys(),
                                "geni_expires": links_db['geni_expires'],
                                "geni_allocation_status": links_db["geni_allocation_status"],
                                "geni_operational_status" : "Not yet implemented"
                            }
                        )


        logger.debug("SE-ManifestFormatter=%s" % (se_manifest,))
        # logger.debug("SE-Slivers(%d)=%s" % (len(links_db), links_db,))


        return {"geni_rspec": "%s" % se_manifest,
                "geni_urn": urns,
                "geni_slivers": result}

    def allocate(self, slice_urn, client_cert, credentials,
                 rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        if self._verify_users:
            logger.debug("allocate: authenticate the user...")
            client_urn, client_uuid, client_email =\
                self.auth(client_cert, credentials, slice_urn, ("createsliver",))
            logger.info("Client urn=%s, uuid=%s, email=%s" % (
                client_urn, client_uuid, client_email,))

        logger.info("slice_urn=%s, end_time=%s, rspec=%s" % (
            slice_urn, end_time, rspec,))
        req_rspec = SERMv3RequestParser(from_string=rspec)
        
        print "\n\n\n\n\n------------------req_rspec >>> ", req_rspec
        self.__validate_rspec(req_rspec.get_rspec())

        se_manifest, se_slivers, se_db_slivers = SERMv3ManifestFormatter(), [], []
        print "\n\n\n\n\n------------------se_manifest >>> ", se_manifest
        print "\n\n\n\n\n------------------se_slivers >>> ", se_slivers
        
        links = req_rspec.links()
        nodes = req_rspec.nodes()

        # check if the requested resources (ports, vlans) are available
        reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)
        availability_result = self.SEResources.check_available_resources(reservation_ports['ports'])

        if availability_result != False:

            print "Ports take part: " , reservation_ports

            # Mark resources as reserved
            self.SEResources.set_resource_reservation(reservation_ports['ports'])
            alarm_time = end_time
            #SESchedulerService.get_scheduler().add_job( SEConfigurator.set_resource_reservation(), "date", run_date=end_time, args=reservation_ports['ports'])
            SESchedulerService.get_scheduler().add_job( se_job_release_resources,
                                                        "date",
                                                        run_date=alarm_time,
                                                        args=[datetime.now(),
                                                        reservation_ports['ports'],
                                                        slice_urn])
            #print "manifest  ", se_manifest
            #print "nodes ", nodes
            #print "links", links
            self.SESlices._create_manifest_from_req_n_and_l(se_manifest, nodes,links)
            logger.debug("SE-ManifestFormatter=%s" % (se_manifest,))
                
                     
            s =  self.SESlices._allocate_ports_in_slice(nodes) 
            print "seslice ports ",s
            
            logger.debug("requested SE-Sliver(%d)=%s" % (len(se_slivers), se_slivers,))
            #link_additional_info={}
            
            print "check link db before operation :", self.SESlices.get_link_db(slice_urn)
            self.SESlices.set_link_db(slice_urn, end_time,links, nodes)
            print "check link db after operation", self.SESlices.get_link_db()
            

            links_db, nodes, links = self.SESlices.get_link_db(slice_urn)

            se_slivers.append(links_db)
            #id_ = db_sync_manager.store_slice_info(slice_urn, se_db_slivers)
            logger.info("allocate successfully completed: %s", slice_urn)
            #self.__schedule_slice_release(end_time, se_db_slivers)
            print "WWWWWWWWWW: %s", se_slivers
            return ("%s" % se_manifest, se_slivers)

        else:
            raise geni_ex.GENIv3GeneralError("Allocation Failed. Requested resources are not available.")


    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
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
        se_manifest, se_slivers, last_slice = SERMv3ManifestFormatter(), [], ""

        for urn in urns:
            if self._verify_users:
                logger.debug("provision: authenticate the user...")
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("renewsliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            logger.info("urn=%s, best_effort=%s, end_time=%s, geni_users=%s" % (
                urn, best_effort, end_time, geni_users,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)
            self.SESlices._create_manifest_from_req_n_and_l(se_manifest, nodes,links)

            reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)["ports"]

            in_port = int(reservation_ports[0]["port"].rsplit(":", 1)[1])
            out_port = int(reservation_ports[1]["port"].rsplit(":", 1)[1])
            in_vlan = int(reservation_ports[0]["vlan"])
            out_vlan = int(reservation_ports[1]["vlan"])

            se_provision.addSwitchingRule(in_port, out_port, in_vlan, out_vlan)

        slivers = [{'geni_sliver_urn' : urns[0],
                    "geni_allocation_status"  : "geni_allocated",
                    "geni_operational_status" : "geni_ready",
                    "geni_expires"         : end_time
                    }
                ]

        return str(se_manifest), slivers

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        slice_urn = urns[0]
        result = []

        for urn in urns:
            if self._verify_users:
                logger.debug("status: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)

            expires_date = datetime.strptime(links_db['geni_expires'], RFC3339_FORMAT_STRING)

            result.append( 
                            {   
                                "geni_sliver_urn": urn,
                                "geni_expires": expires_date,
                                "geni_allocation_status": links_db["geni_allocation_status"],
                                "geni_operational_status" : "Ready"
                            }
                        )


        return slice_urn, result

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        raise geni_ex.GENIv3GeneralError("unsupported method")

    def delete(self, urns, client_cert, credentials, best_effort):     ### FIX the response
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        result = []

        for urn in urns:
            if self._verify_users:
                logger.debug("delete: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("deletesliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)
            reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)

            reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)["ports"]

            in_port = int(reservation_ports[0]["port"].rsplit(":", 1)[1])
            out_port = int(reservation_ports[1]["port"].rsplit(":", 1)[1])
            in_vlan = int(reservation_ports[0]["vlan"])
            out_vlan = int(reservation_ports[1]["vlan"])

            se_provision.deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan)

            # expires_date = datetime.strptime(links_db['geni_expires'], RFC3339_FORMAT_STRING)
            expires_date = links_db['geni_expires']


            result.append( 
                {   
                    "geni_sliver_urn": urn,# links_db['geni_sliver_urn'][0].keys(),
                    "geni_expires": expires_date,
                    "geni_allocation_status": links_db["geni_allocation_status"],
                    "geni_operational_status" : "Not yet implemented"
                }
            )

            # Mark resources as free
            self.SEResources.free_resource_reservation(reservation_ports)

            # Remove reservation
            self.SESlices.remove_link_db(urn)

        # logger.info("best_effort=%s" % (best_effort,))

        # route = db_sync_manager.get_slice_routing_keys(urns)
        # logger.debug("Route=%s" % (route,))

        # for r, v in route.iteritems():
        #     peer = db_sync_manager.get_configured_peer(r)
        #     logger.debug("peer=%s" % (peer,))
        #     if peer.get("type") in ["sdn_networking", "transport_network",
        #                             "stitching_entity"]:
        #         slivers = self.__manage_delete(
        #             peer, v, credentials, best_effort)

        #         logger.debug("slivers=%s" % (slivers,))
        #         ro_slivers.extend(slivers)

        # db_urns = []
        # for s in ro_slivers:
        #     s["geni_expires"] = self.__str2datetime(s["geni_expires"])
        #     db_urns.append(s.get("geni_sliver_urn"))
        # logger.debug("RO-Slivers(%d)=%s, DB-URNs(%d)=%s" %
        #              (len(ro_slivers), ro_slivers, len(db_urns), db_urns))

        # db_sync_manager.delete_slice_urns(db_urns)

        return result

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

    # def __update_sdn_route(self, route, values):
    #     for v in values:
    #         for dpid in v.get("dpids"):
    #             k = db_sync_manager.get_sdn_datapath_routing_key(dpid)
    #             dpid["routing_key"] = k
    #             if k not in route:
    #                 sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #                 route[k] = OFv3RequestFormatter(schema_location=sl)

    # def __update_sdn_route_rspec(self, route, sliver, controllers,
    #                              groups, matches):
    #     for key, rspec in route.iteritems():
    #         rspec.sliver(sliver.get("description"),
    #                      sliver.get("ref"),
    #                      sliver.get("email"))
    #         for c in controllers:
    #             rspec.controller(c.get("url"), c.get("type"))
    #         for g in groups:
    #             rspec.group(g.get("name"))
    #             for dpid in g.get("dpids"):
    #                 if dpid.get("routing_key") == key:
    #                     rspec.group_datapath(g.get("name"), dpid)
    #         for m in matches:
    #             match = Match()
    #             for uf in m.get("use_groups"):
    #                 match.add_use_group(uf.get("name"))
    #             for dpid in m.get("dpids"):
    #                 if dpid.get("routing_key") == key:
    #                     match.add_datapath(dpid)
    #             match.set_packet(m.get("packet").get("dl_src"),
    #                              m.get("packet").get("dl_dst"),
    #                              m.get("packet").get("dl_type"),
    #                              m.get("packet").get("dl_vlan"),
    #                              m.get("packet").get("nw_src"),
    #                              m.get("packet").get("nw_dst"),
    #                              m.get("packet").get("nw_proto"),
    #                              m.get("packet").get("tp_src"),
    #                              m.get("packet").get("tp_dst"))
    #             rspec.match(match.serialize())

    # def __send_request_rspec(self, routing_key, req_rspec, slice_urn,
    #                          credentials, end_time):
    #     peer = db_sync_manager.get_configured_peer(routing_key)
    #     logger.debug("Peer=%s" % (peer,))
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     logger.debug("Adaptor=%s" % (adaptor,))
    #     return adaptor.allocate(slice_urn, credentials[0]["geni_value"],
    #                             "%s" % req_rspec, end_time)

    # def __extend_slivers(self, values, routing_key, slivers, db_slivers):
    #     logger.info("Slivers=%s" % (values,))
    #     slivers.extend(values)
    #     for dbs in values:
    #         db_slivers.append({"geni_sliver_urn": dbs.get("geni_sliver_urn"),
    #                            "routing_key": routing_key})

    # def __extract_se_from_sdn(self, groups, matches):
    #     ret = []
    #     for m in matches:
    #         vlan_id = m.get('packet').get('dl_vlan')
    #         if vlan_id is None:
    #             continue

    #         dpids = []
    #         for mg in m.get('use_groups'):
    #             for g in groups:
    #                 if g.get('name') == mg.get('name'):
    #                     for gds in g.get('dpids'):
    #                         dpids.append(gds.get('component_id'))

    #         for mds in m.get('dpids'):
    #             dpids.append(mds.get('component_id'))

    #         if len(dpids) > 0:
    #             ret.append({'vlan': vlan_id, 'dpids': dpids})

    #     return ret

    # def __update_com_route(self, route, values):
    #     for v in values:
    #         cid = v.get("component_id")
    #         k = db_sync_manager.get_com_node_routing_key(cid)
    #         v["routing_key"] = k
    #         if k not in route:
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = CRMv3RequestFormatter(schema_location=sl)

    # def __update_com_route_rspec(self, route, slivers):
    #     for key, rspec in route.iteritems():
    #         for s in slivers:
    #             if s.get("routing_key") == key:
    #                 rspec.node(s)

#     def __manage_com_allocate(self, slice_urn, credentials,
#                               slice_expiration, slivers, parser):
#         # FIXME This is not working
#         route = {}
#         self.__update_com_route(route, slivers)
#         logger.debug("Slivers=%s" % (slivers,))
# 
#         self.__update_com_route_rspec(route, slivers)
#         logger.info("Route=%s" % (route,))
#         manifests, slivers, db_slivers = [], [], []
# 
#         print "\n\n\n\n\n\n\n> route: ", route
#         for k, v in route.iteritems():
#             (m, ss) = self.__send_request_rspec(
#                 k, v, slice_urn, credentials, slice_expiration)
#             logger.debug("\n\n\n\n\n\n\ndelegate > manifest: %s\n\n\n\n\n\n\n" % str(m))
#             manifest = CRMv3ManifestParser(from_string=m)
#             logger.debug("CRMv3ManifestParser=%s" % (manifest,))
# 
#             sliver = manifest.sliver()
#             logger.info("Sliver=%s" % (sliver,))
#             manifests.append(sliver)
# 
#             self.__extend_slivers(ss, k, slivers, db_slivers)
# 
#         return (manifests, slivers, db_slivers)

    # def __manage_sdn_allocate(self, surn, creds, end, sliver, parser):
    #     route = {}
    #     controllers = parser.of_controllers()
    #     logger.debug("Controllers=%s" % (controllers,))

    #     groups = parser.of_groups()
    #     self.__update_sdn_route(route, groups)
    #     logger.debug("Groups=%s" % (groups,))

    #     matches = parser.of_matches()
    #     self.__update_sdn_route(route, matches)
    #     logger.debug("Matches=%s" % (matches,))

    #     se_sdn_info = self.__extract_se_from_sdn(groups, matches)
    #     logger.debug("SE-SDN-INFO=%s" % (se_sdn_info,))

    #     self.__update_sdn_route_rspec(route, sliver, controllers, groups,
    #                                   matches)
    #     logger.info("Route=%s" % (route,))
    #     manifests, slivers, db_slivers = [], [], []

    #     for k, v in route.iteritems():
    #         (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
    #         manifest = OFv3ManifestParser(from_string=m)
    #         logger.debug("OFv3ManifestParser=%s" % (manifest,))

    #         sliver = manifest.sliver()
    #         logger.info("Sliver=%s" % (sliver,))
    #         manifests.append(sliver)

    #         self.__extend_slivers(ss, k, slivers, db_slivers)

    #     return (manifests, slivers, db_slivers, se_sdn_info)

    # def __update_tn_node_route(self, route, values):
    #     for v in values:
    #         k = db_sync_manager.get_tn_node_routing_key(v.get("component_id"))
    #         v["routing_key"] = k
    #         if k not in route:
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = TNRMv3RequestFormatter(schema_location=sl)

    # def __update_tn_link_route(self, route, values):
    #     for v in values:
    #         k = db_sync_manager.get_tn_link_routing_key(
    #             v.get("component_id"), v.get("component_manager_name"),
    #             [i.get("component_id") for i in v.get("interface_ref")])
    #         v["routing_key"] = k
    #         if k not in route:
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = TNRMv3RequestFormatter(schema_location=sl)
                
    # def __update_se_node_route(self, route, values):
    #     for v in values:
    #         k = db_sync_manager.get_se_node_routing_key(v.get("component_id"))
    #         v["routing_key"] = k
    #         if k not in route:
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = SERMv3RequestFormatter(schema_location=sl)

    # def __update_se_link_route(self, route, values):
    #     for v in values:
    #         k = db_sync_manager.get_se_link_routing_key(
    #             v.get("component_id"), v.get("component_manager_name"),
    #             [i.get("component_id") for i in v.get("interface_ref")])
    #         v["routing_key"] = k
    #         if k not in route:
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = SERMv3RequestFormatter(schema_location=sl)

    # def __update_tn_route_rspec(self, route, nodes, links):
    #     for key, rspec in route.iteritems():
    #         for n in nodes:
    #             if n.get("routing_key") == key:
    #                 rspec.node(n)
    #         for l in links:
    #             if l.get("routing_key") == key:
    #                 rspec.link(l)

    # def __extract_se_from_tn(self, nodes, links):
    #     ret, ifref = [], set()
    #     for l in links:
    #         for p in l.get('property'):
    #             ifref.add(p.get('source_id'))
    #             ifref.add(p.get('dest_id'))

    #     for n in nodes:
    #         for i in n.get('interfaces'):
    #             if i.get('component_id') in ifref:
    #                 for v in i.get('vlan'):
    #                     ret.append({'vlan': v.get('tag'),
    #                                 'interface': i.get('component_id')})

    #     return ret

    # def __manage_tn_allocate(self, surn, creds, end, nodes, links):
    #     route = {}
    #     self.__update_tn_node_route(route, nodes)
    #     logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
    #     self.__update_tn_link_route(route, links)
    #     logger.debug("Links(%d)=%s" % (len(links), links,))

    #     self.__update_tn_route_rspec(route, nodes, links)
    #     logger.info("Route=%s" % (route,))

    #     manifests, slivers, db_slivers, se_tn_info = [], [], [], []

    #     for k, v in route.iteritems():
    #         (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
    #         manifest = TNRMv3ManifestParser(from_string=m)
    #         logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
    #         self.__validate_rspec(manifest.get_rspec())

    #         nodes = manifest.nodes()
    #         logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
    #         links = manifest.links()
    #         logger.info("Links(%d)=%s" % (len(links), links,))

    #         manifests.append({"nodes": nodes, "links": links})

    #         self.__extend_slivers(ss, k, slivers, db_slivers)

    #         se_tn = self.__extract_se_from_tn(nodes, links)
    #         logger.debug("SE-TN-INFO=%s" % (se_tn,))
    #         if len(se_tn) > 0:
    #             se_tn_info.extend(se_tn)

    #     return (manifests, slivers, db_slivers, se_tn_info)

    # def __update_se_info_route(self, route, values, key):
    #     for v in values:
    #         k, ifs = db_sync_manager.get_se_link_routing_key(v.get(key))
    #         v['routing_key'] = k
    #         v['internal_ifs'] = ifs
    #         node = db_sync_manager.get_se_node_info(k)
    #         v['node'] = node
    #         if (k is not None) and (k not in route):
    #             sl = "http://www.geni.net/resources/rspec/3/request.xsd"
    #             route[k] = SERMv3RequestFormatter(schema_location=sl)

    # def __update_se_nodes(self, nodes, values):
    #     for v in values:
    #         if v.get('node') is not None:
    #             cid = v.get('node').get('component_id')
    #             cmid = v.get('node').get('component_manager_id')
    #             if len(nodes) > 0:
    #                 for i in nodes:
    #                     if (i.serialize().get('component_id') != cid) and\
    #                        (i.serialize().get('component_manager_id') != cmid):
    #                         n = Node(cid, cmid,
    #                                  sliver_type_name=v.get('routing_key'))
    #                         nodes.append(n)
    #             else:
    #                 n = Node(cid, cmid, sliver_type_name=v.get('routing_key'))
    #                 nodes.append(n)

    #     for v in values:
    #         if v.get('node') is not None:
    #             for n in nodes:
    #                 scid = v.get('node').get('component_id')
    #                 scmid = v.get('node').get('component_manager_id')
    #                 ncid = n.serialize().get('component_id')
    #                 ncmid = n.serialize().get('component_manager_id')
    #                 if (scid == ncid) and (scmid == ncmid):
    #                     for i in v.get('internal_ifs'):
    #                         intf = Interface(i.get('component_id'))
    #                         intf.add_vlan(v.get('vlan'), "")
    #                         n.add_interface(intf.serialize())

    # def __create_selink(self, if1, if2, sliver_id):
    #     i = if1.rindex(':')
    #     n1, name1 = if1[0:i], if1[i+1:len(if1)]
    #     i = if2.rindex(':')
    #     n2, name2 = if2[0:i], if2[i+1:len(if1)]

    #     if n1 != n2:
    #         raise Exception("SELink: differs node cid (%s,%s)" % (n1, n2))

    #     cid = n1 + ':' + name1 + '-' + name2
    #     typee, cm_name = db_sync_manager.get_se_link_info(n1)

    #     l = SELink(cid, typee, cm_name, sliver=sliver_id)
    #     l.add_interface_ref(if1)
    #     l.add_interface_ref(if2)
    #     return l

    # def __update_se_link(self, links, svalues, tvalues):
    #     for s in svalues:
    #         for sintf in s.get('internal_ifs'):
    #             for t in tvalues:
    #                 for tintf in t.get('internal_ifs'):
    #                     if s.get('routing_key') == t.get('routing_key'):
    #                         l = self.__create_selink(sintf.get('component_id'),
    #                                                  tintf.get('component_id'),
    #                                                  s.get('routing_key'))
    #                         links.append(l)

    # def __extract_se_info(self, sdn, tn):
    #     nodes, links = [], []
    #     self.__update_se_nodes(nodes, sdn)
    #     self.__update_se_nodes(nodes, tn)
    #     self.__update_se_link(links, sdn, tn)

    #     return [n.serialize() for n in nodes], [l.serialize() for l in links]

    # def __update_se_route_rspec(self, route, sdn_info, tn_info):
    #     nodes, links = self.__extract_se_info(sdn_info, tn_info)
    #     logger.debug("SE-Nodes=%s" % (nodes,))
    #     logger.debug("SE-Links=%s" % (links,))

    #     for key, rspec in route.iteritems():
    #         for n in nodes:
    #             if n.get("sliver_type_name") == key:
    #                 n["sliver_type_name"] = None
    #                 rspec.node(n)
    #         for l in links:
    #             if l.get("sliver_id") == key:
    #                 l["sliver"] = None
    #                 rspec.link(l)

    # def __manage_se_allocate2(self, surn, creds, end, nodes, links):
    #     route = {}
    #     #self.__update_se_node_route(route, nodes)
        
    #     logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
    #     #self.__update_se_link_route(route, links)
        
    #     logger.debug("Links(%d)=%s" % (len(links), links,))

    #     #self.__update_se_route_rspec(route, nodes, links)
    #     logger.info("Route=%s" % (route,))

    #     manifests, slivers, db_slivers= [], [], [],

    #     for k, v in route.iteritems():
    #         print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    #         (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
    #         print"manifest",m
    #         manifest = SERMv3ManifestParser(from_string=m)
    #         logger.debug("SERMv3ManifestParser=%s" % (manifest,))
    #         self.__validate_rspec(manifest.get_rspec())
            
            
    #         nodes = manifest.nodes()
    #         logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
    #         links = manifest.links()
    #         logger.info("Links(%d)=%s" % (len(links), links,))

    #         manifests.append({"nodes": nodes, "links": links})

    #         self.__extend_slivers(ss, k, slivers, db_slivers)

    #         #se_tn = self.__extract_se_from_tn(nodes, links)
    #         #logger.debug("SE-TN-INFO=%s" % (se_tn,))
    #         #if len(se_tn) > 0:
    #         #    se_tn_info.extend(se_tn)

    #     return (manifests, slivers, db_slivers) 

    # def __manage_se_allocate(self, surn, creds, end, sdn_info, tn_info):
    #     route = {}
    #     self.__update_se_info_route(route, sdn_info, 'dpids')
    #     logger.debug("SE-SdnInfo(%d)=%s" % (len(sdn_info), sdn_info,))
    #     self.__update_se_info_route(route, tn_info, 'interface')
    #     logger.debug("SE-TnInfo(%d)=%s" % (len(tn_info), tn_info,))

    #     self.__update_se_route_rspec(route, sdn_info, tn_info)
    #     logger.info("Route=%s" % (route,))

    #     manifests, slivers, db_slivers = [], [], []

    #     for k, v in route.iteritems():
    #         (m, ss) = self.__send_request_rspec(k, v, surn, creds, end)
    #         manifest = SERMv3ManifestParser(from_string=m)
    #         logger.debug("SERMv3ManifestParser=%s" % (manifest,))
    #         self.__validate_rspec(manifest.get_rspec())

    #         nodes = manifest.nodes()
    #         logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
    #         links = manifest.links()
    #         logger.info("Links(%d)=%s" % (len(links), links,))

    #         manifests.append({"nodes": nodes, "links": links})

    #         self.__extend_slivers(ss, k, slivers, db_slivers)

    #     return (manifests, slivers, db_slivers)

    # def __manage_sdn_describe(self, peer, urns, creds):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

    #     manifest = OFv3ManifestParser(from_string=m)
    #     logger.debug("OFv3ManifestParser=%s" % (manifest,))
    #     # self.__validate_rspec(manifest.get_rspec())

    #     sliver = manifest.sliver()
    #     logger.info("Sliver=%s" % (sliver,))

    #     return (sliver, urn, ss)

    # def __manage_tn_describe(self, peer, urns, creds):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

    #     manifest = TNRMv3ManifestParser(from_string=m)
    #     logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
    #     self.__validate_rspec(manifest.get_rspec())

    #     nodes = manifest.nodes()
    #     logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
    #     links = manifest.links()
    #     logger.info("Links(%d)=%s" % (len(links), links,))

    #     return ({"nodes": nodes, "links": links}, urn, ss)

    # def __manage_se_describe(self, peer, urns, creds):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

    #     manifest = SERMv3ManifestParser(from_string=m)
    #     logger.debug("SERMv3ManifestParser=%s" % (manifest,))
    #     self.__validate_rspec(manifest.get_rspec())

    #     nodes = manifest.nodes()
    #     logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
    #     links = manifest.links()
    #     logger.info("Links(%d)=%s" % (len(links), links,))

    #     return ({"nodes": nodes, "links": links}, urn, ss)

    # def __manage_status(self, peer, urns, creds):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     return adaptor.status(urns, creds[0]["geni_value"])

    # def __manage_renew(self, peer, urns, creds, etime, beffort):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     return adaptor.renew(urns, creds[0]["geni_value"], etime, beffort)

    # def __manage_operational_action(self, peer, urns, creds, action, beffort):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     return adaptor.perform_operational_action(
    #         urns, creds[0]["geni_value"], action, beffort)

    # def __manage_delete(self, peer, urns, creds, beffort):
    #     adaptor = AdaptorFactory.create_from_db(peer)
    #     return adaptor.delete(urns, creds[0]["geni_value"], beffort)

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

#     def __translate_action(self, geni_action):
#         if geni_action == self.OPERATIONAL_ACTION_STOP:
#             return "stopslice"
#         elif geni_action == self.OPERATIONAL_ACTION_START:
#             return "startslice"
#         return "unknown"

#     def __schedule_slice_release(self, end_time, slivers):
#         pass
# #         #scheduler = ROSchedulerService.get_scheduler()
# #         logger.debug("schedule_slice_release: endtime=%s, slivers=%s, obj=%s" %
# #                      (end_time, slivers, scheduler,))
# #         if (end_time is not None) and (scheduler is not None):
# #             urns = [s.get("geni_sliver_urn") for s in slivers]
# #             ROSchedulerService.get_scheduler().add_job(
# #                 slice_expiration, "date", run_date=end_time, args=[urns])

#     # Helper methods
#     def _get_sliver_status_hash(self, lease, include_allocation_status=False,
#                                 include_operational_status=False,
#                                 error_message=None):
#         """Helper method to create the sliver_status return
#         values of allocate and other calls."""
#         result = {"geni_sliver_urn": self._ip_to_urn(str(lease["ip_str"])),
#                   "geni_expires": lease["end_time"],
#                   "geni_allocation_status": self.ALLOCATION_STATE_ALLOCATED}

#         result["geni_allocation_status"] = self.ALLOCATION_STATE_UNALLOCATED\
#             if lease["available"] else self.ALLOCATION_STATE_PROVISIONED

#         # there is no state to an ip, so we always return ready
#         if (include_operational_status):
#             result["geni_operational_status"] = self.OPERATIONAL_STATE_READY

#         if (error_message):
#             result["geni_error"] = error_message

#         return result

    # def _get_manifest_rspec(self, leases):
    #     E = self.lxml_manifest_element_maker("resource-orchestrator")
    #     manifest = self.lxml_manifest_root()
    #     for lease in leases:
    #         # assemble manifest
    #         r = E.resource()
    #         r.append(E.ip(lease["ip_str"]))
    #         # TODO add more info here
    #     logger.debug("manifest=%s", (manifest,))
