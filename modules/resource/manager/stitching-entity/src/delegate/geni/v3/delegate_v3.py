import importlib
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
from delegate.geni.v3.db_manager_se import db_sync_manager


# dynamic import of SE provision plugin depending on config settings
se_provision = __import__(SEConfigurator.seConfigurator().get_provision_plugin(), globals(), locals(), [], -1)

from datetime import datetime, timedelta
from delegate.geni.v3.se_scheduler import SESchedulerService


logger = core.log.getLogger("geniv3delegate")

test_links_db = {}
link_additional_info={}

RFC3339_FORMAT_STRING = "%Y-%m-%d %H:%M:%S.%fZ"

def getPortsVlansPairs(links_db):
    portsVlansPairs=[]
    for sliver in links_db["geni_sliver_urn"]:
        dpid, in_port, dpid, out_port, in_vlan, out_vlan = sliver.split("+")[-1].split("_")
        portsVlansPairs.append((in_port, out_port, in_vlan, out_vlan))
    return portsVlansPairs

def se_job_release_resources(time, ports, slice_urn):

    
    SEResources = SEConfigurator.seConfigurator()
    
    SESlices = seSlicesWithSlivers()

    logger.info('Release! This was scheduled at %s Resources: %s Slice URN: %s' % (time, ports, slice_urn))

    # Mark resources as free
    SEResources.free_resource_reservation(ports)

    # Remove reservation
    db_sync_manager.remove_slices(slice_urn)

def se_job_unprovision(time, links_db, slice_urn):

    portsVlansPairs = getPortsVlansPairs(links_db)

    try:
        for portVlanItem in portsVlansPairs:
            (in_port, out_port, in_vlan, out_vlan) = portVlanItem
            se_provision.deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan)
    except:
        logger.error("Unprovisioning slice error. Problem in communication with SE")

class GENIv3Delegate(GENIv3DelegateBase):
    """
    """

    
    def __init__(self,path=None):
        super(GENIv3Delegate, self).__init__()

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

        links = self.SEResources.get_links_dict_for_rspec(geni_available)
        nodes = self.SEResources.get_nodes_dict_for_rspec(geni_available)

        try:
             print "ALL LINKS: ", links
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
                                "geni_sliver_urn": links_db['geni_sliver_urn'],
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
        # TODO: Check if sliver_urn is valid for RO
        result = []
        #Default end time = 30 days
        default_end_time = datetime.now() + timedelta(days=30)
        if end_time == None:

            print "###################################    time default   ", default_end_time
            end_time = default_end_time
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
        
        # vlanPairsResult = self.__getVlanPairs(req_rspec)

        print "\n\n\n\n\n------------------req_rspec >>> ", req_rspec

        links = req_rspec.links()
        nodes = req_rspec.nodes()

        # Workaround for "1:n" case: Get Vlan pairs from link->felix:vlan param
        sliceVlansPairs = req_rspec.getVlanPairs()

        # check if the requested resources (ports, vlans) are available
        reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)
        availability_result = self.SEResources.check_available_resources(reservation_ports['ports'])

        if availability_result != False:

            # Mark resources as reserved
            self.SEResources.set_resource_reservation(reservation_ports['ports'])
            if end_time != None:
                alarm_time = end_time
                SESchedulerService.get_scheduler().add_job( se_job_release_resources,
                                                            "date",
                                                            run_date=alarm_time,
                                                            args=[datetime.now(),
                                                            reservation_ports['ports'],
                                                            slice_urn])

            self.SESlices._create_manifest_from_req_n_and_l(se_manifest, nodes,links, sliceVlansPairs)
            logger.debug("SE-ManifestFormatter=%s" % (se_manifest,))

            s =  self.SESlices._allocate_ports_in_slice(nodes) 
                        
            self.SESlices.set_link_db(slice_urn, end_time,links, nodes, sliceVlansPairs)
            

            links_db, nodes, links = self.SESlices.get_link_db(slice_urn)
            for sliver in links_db["geni_sliver_urn"]:
                result.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": links_db['geni_expires'],
                                    "geni_allocation_status": links_db["geni_allocation_status"],
                                    "geni_operational_status" : links_db["geni_operational_status"]
                                }
                            )

            se_slivers = result
            logger.info("allocate successfully completed: %s", slice_urn)
            logger.debug("requested SE-Sliver(%d)=%s" % (len(se_slivers), se_slivers,))
            return ("%s" % se_manifest, se_slivers)

        else:
            raise geni_ex.GENIv3GeneralError("Allocation Failed. Requested resources are not available.")


    def renew(self, urns, client_cert, credentials, expiration_time,best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""

        slice_urn = urns[0]
        result = []


        for urn in urns:
            if self._verify_users:
                logger.debug("renew: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("renewsliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            logger.info("current expiration_time=%s, best_effort=%s" % (expiration_time, best_effort,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)
            self.SESlices.set_link_db(urn,expiration_time,links,nodes,sliceVlansPairs=None) # TODO: Fix missing sliceVlansPairs

            logger.info("new expiration_time=%s" % (expiration_time,))
            
            # expires_date = datetime.strptime(links_db['geni_expires'], RFC3339_FORMAT_STRING)

            for sliver in links_db["geni_sliver_urn"]:
                result.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": expiration_time,
                                    "geni_allocation_status": links_db["geni_allocation_status"],
                                    "geni_operational_status" : "geni_notready"
                                }
                            )

        return  slice_urn,result

    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        se_manifest, se_slivers, last_slice = SERMv3ManifestFormatter(), [], ""
        slivers=[]

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
            sliceVlansPairs = self.SESlices.get_slice_vlan_pairs(urn)
            self.SESlices._create_manifest_from_req_n_and_l(se_manifest, nodes,links, sliceVlansPairs)

            reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)["ports"]

            if end_time != None:
                alarm_time = end_time
                SESchedulerService.get_scheduler().add_job( se_job_unprovision,
                                                            "date",
                                                            run_date=alarm_time,
                                                            args=[datetime.now(),
                                                            links_db,
                                                            urn])

            for sliver in links_db["geni_sliver_urn"]:
                slivers.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": end_time,
                                    "geni_allocation_status": "geni_provisioned",
                                    "geni_operational_status" : "geni_notready"
                                }
                            )


            logger.info("provision successfully completed: %s", urn)

        return str(se_manifest), slivers

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        slice_urn = urns[0]
        slivers = []

        for urn in urns:
            if self._verify_users:
                logger.debug("status: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)

            # expires_date = datetime.strptime(links_db['geni_expires'], RFC3339_FORMAT_STRING)
            expires_date = links_db['geni_expires']

            for sliver in links_db["geni_sliver_urn"]:
                slivers.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": expires_date,
                                    "geni_allocation_status": links_db["geni_allocation_status"],
                                    "geni_operational_status" : "geni_ready"
                                }
                            )

        return slice_urn, slivers

    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        result = []
        status = ""

        for urn in urns:
            if self._verify_users: ### TODO: Fix authentication
                logger.debug("status: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("sliverstatus",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)

            expires_date = links_db['geni_expires']

            # reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)["ports"]

            portsVlansPairs = getPortsVlansPairs(links_db)

            if action == "start":
                for portVlanItem in portsVlansPairs:
                    (in_port, out_port, in_vlan, out_vlan) = portVlanItem
                    print in_port, in_vlan, out_port, out_vlan
                    try:
                        se_provision.addSwitchingRule(in_port, out_port, in_vlan, out_vlan)
                    except e:
                        print e
                        raise geni_ex.GENIv3GeneralError("Error in communication with SE.")
                    logger.debug("Cross-connection added: %s[%s]<->%s[%s]" % (in_port, in_vlan, out_port, out_vlan))
                status = "geni_ready"

            elif action == "stop":
                for portVlanItem in portsVlansPairs:
                    (in_port, out_port, in_vlan, out_vlan) = portVlanItem
                    try:
                        se_provision.deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan)
                    except:
                        raise geni_ex.GENIv3GeneralError("Error in communication with SE.")
                    logger.debug("Cross-connection deleted: %s[%s]<->%s[%s]" % (in_port, in_vlan, out_port, out_vlan))

                status = "geni_notready"
                
            elif action == "restart":
                for portVlanItem in portsVlansPairs:
                    (in_port, out_port, in_vlan, out_vlan) = portVlanItem
                    try:
                        se_provision.deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan)
                        se_provision.addSwitchingRule(in_port, out_port, in_vlan, out_vlan)
                    except:
                        raise geni_ex.GENIv3GeneralError("Error in communication with SE.")
                status = "geni_ready"


            for sliver in links_db["geni_sliver_urn"]:
                result.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": expires_date,
                                    "geni_allocation_status": links_db["geni_allocation_status"],
                                    "geni_operational_status" : status
                                }
                            )

        return result

    def delete(self, urns, client_cert, credentials, best_effort):     ### FIX the response
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        result = []
        slice_urn = urns[0]
        # try:
        for urn in urns:
            if self._verify_users:
                logger.debug("delete: authenticate the user for %s" % (urn))
                client_urn, client_uuid, client_email =\
                    self.auth(client_cert, credentials, urn, ("deletesliver",))
                logger.info("Client urn=%s, uuid=%s, email=%s" % (
                    client_urn, client_uuid, client_email,))

            links_db, nodes, links = self.SESlices.get_link_db(urn)

            reservation_ports = self.SESlices._allocate_ports_in_slice(nodes)["ports"]

            portsVlansPairs = getPortsVlansPairs(links_db)

            try:
                for portVlanItem in portsVlansPairs:
                    (in_port, out_port, in_vlan, out_vlan) = portVlanItem
                    se_provision.deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan)
            except:
                logger.warning("Problem in communication with SE")

            # expires_date = datetime.strptime(links_db['geni_expires'], RFC3339_FORMAT_STRING)
            expires_date = links_db['geni_expires']

            logger.debug("unprovision SE-Slice-Urn=%s, in_port=%s , out_port=%s,  in_vlan=%s,  out_port=%s" % (urn,in_port, out_port, in_vlan, out_vlan))

            for sliver in links_db["geni_sliver_urn"]:
                result.append( 
                                {   
                                    "geni_sliver_urn": sliver,
                                    "geni_expires": expires_date,
                                    "geni_allocation_status": "geni_unallocated",
                                    "geni_operational_status" : "geni_notready"
                                }
                            )

            # Mark resources as free
            self.SEResources.free_resource_reservation(reservation_ports)

            # Remove reservation
            self.SESlices.remove_link_db(urn)
            
            logger.info("delete successfully completed: %s", slice_urn)
    
            return result

        # except:

        #     raise geni_ex.GENIv3GeneralError("Delete Failed. Requested resources are not available.")

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


    ### Helper methods ###

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

    # def __getVlanPairs(self, req_rspec):
    #     links_ = []
    #     for l in self.rspec.findall(".//{%s}link" % (self.none)):
    #         manager_ = l.find("{%s}component_manager" % (self.none))
    #         if manager_ is None:
    #             self.raise_exception("Component-Mgr tag not found in link!")

    #         type_ = l.find("{%s}link_type" % (self.none))
    #         if type_ is None:
    #             self.raise_exception("Link-Type tag not found in link!")

    #         l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
    #                     manager_.attrib.get("name"))

    #         [l_.add_interface_ref(i.attrib.get("client_id"))
    #          for i in l.iterfind("{%s}interface_ref" % (self.none))]

    #         [l_.add_property(p.attrib.get("source_id"),
    #                          p.attrib.get("dest_id"),
    #                          p.attrib.get("capacity"))
    #          for p in l.iterfind("{%s}property" % (self.none))]

    #         links_.append(l_.serialize())

    #     return links_
