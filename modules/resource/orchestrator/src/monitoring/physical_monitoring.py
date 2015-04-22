from db.db_manager import db_sync_manager
from monitoring.base_monitoring import BaseMonitoring

import core
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-physical")


class PhysicalMonitoring(BaseMonitoring):
    """
    Periodically communicates physical topology to the MS.
    """

    def __init__(self):
        super(PhysicalMonitoring, self).__init__()

#    def retrieve_topology(self, peer):
#        # General information
#        self.__add_general_info()
#        # COM resources
#        self._add_com_info()
#        # SDN resources
#        self._add_sdn_info()
#        # TN resources
#        self._add_tn_info()
#        # SE resources
#        self._add_se_info()

    def retrieve_topology_per_peer(self, peer_urn):
        # Prepare list of allowed peers and resources
        type_resources_crm = ["crm"]
        type_resources_crm.extend(self.urn_type_resources_variations.get("crm"))
        type_resources_sdnrm = ["sdnrm"]
        type_resources_sdnrm.extend(self.urn_type_resources_variations.get("sdnrm"))
        type_resources_serm = ["serm"]
        type_resources_serm.extend(self.urn_type_resources_variations.get("serm"))
        type_resources_tnrm = ["tnrm"]
        type_resources_tnrm.extend(self.urn_type_resources_variations.get("tnrm"))

        type_resources = []        
        type_resources.extend(type_resources_crm)
        type_resources.extend(type_resources_sdnrm)
        type_resources.extend(type_resources_serm)
        type_resources.extend(type_resources_tnrm)

        # If the URN contains one 
        type_resource_peer = None
        for type_resource in type_resources:
            if type_resource in peer_urn:
                type_resource_peer = type_resource
                break
        # COM resources
        if type_resource_peer in type_resources_crm:
            self._add_com_info()
        # SDN resources
        elif type_resource_peer in type_resources_sdnrm:
            self._add_sdn_info()
        # TN resources (fix in URN...)
        elif type_resource_peer in type_resources_tnrm:
            self._add_tn_info()
        # SE resources
        elif type_resource_peer in type_resources_serm:
            self._add_se_info()

    def send_topology(self, monitoring_server):
        logger.debug("Configured peers=%d" % (len(self.peers)))
        for domain_name, peers in self.peers_by_domain.iteritems():
            try:
                # Update domain URN with name
                self.domain_urn = domain_name
                db_peers = {}
                for peer in peers:
                    db_peer = db_sync_manager.get_configured_peer_by_urn(peer)
                    # Looks for referred domain through peer ID; retrieve URN and last update
                    filter_params = {"_ref_peer": db_peer.get("_id"),}
                    domain_peer = db_sync_manager.get_domain_info(filter_params)
                    domain_peer_urn = domain_peer.get("domain_urn")
                    physical_topology = db_sync_manager.get_physical_info_from_domain(domain_peer.get("_id"))
                    domain_last_update = physical_topology.get("last_update")
                    db_peers[peer] = {
                        "db_peer": db_peer,
                        "domain_urn": domain_peer_urn,
                        "domain_last_update": domain_last_update,
                    }
                    self.domain_peer_urn = domain_peer_urn
                    # Choose less recent time of last update
                    if self.domain_last_update:
                        if domain_last_update < self.domain_last_update:
                            self.domain_last_update = domain_last_update
                    else:
                        self.domain_last_update = domain_last_update
                # Add general information to the topology
                self.__add_general_info()
                for db_peer in db_peers:
                    # Retrieve proper resources
                    self.retrieve_topology_per_peer(db_peers.get(db_peer).get("domain_urn"))
            except Exception as e:
                logger.warning("Physical topology - Cannot recover information for peer (id='%s'). Skipping to the next peer. Details: %s" % (peer.get("_id"), e))
        # Send topology after all peers are completed
        self._send(self.get_topology(), monitoring_server)
        logger.debug("Resulting RSpec=%s" % self.get_topology_pretty())


    ##########
    # Helpers
    ##########

    def __add_general_info(self):
        """
        Creates new RSpec from scratch.
        """
        topo = ET.SubElement(self.topology_list, "topology")
        # Milliseconds in UTC format
        topo.attrib["last_update_time"] = self.domain_last_update
        topo.attrib["type"] = "physical"
        topo.attrib["name"] = self.domain_urn
        # Set topology tag as root node for subsequent operations
        self.topology = topo

