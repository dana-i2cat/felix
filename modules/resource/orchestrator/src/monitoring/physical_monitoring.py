from db.db_manager import db_sync_manager
from lxml import etree

import core
import time
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-manager")


class PhysicalMonitoring():
    """
    Periodically communicates physical topology to the MS.
    """

    def __init__(self):
        self.peers = [p for p in db_sync_manager.get_configured_peers()]
        self.topology_list = ET.Element("topology_list")
        self.retrieve_topology()

    def retrieve_topology(self):
        logger.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            logger.debug("Peer=%s" % (peer,))
            # General information (
            self.__add_general_info()
            # COM resources
            self.__add_com_info()
            # SDN resources
            self.__add_sdn_info()
            # TN resources
            self.__add_tn_info()
            # SE resources
            self.__add_se_info()
        logger.debug("Resulting RSpec=%s" % self.get_topology_pretty())

    ##################
    # Return topology
    ##################

    def get_topology_tree(self):
        # Return whole list of topologies
        return self.topology_list

    def get_topology(self):
        return ET.tostring(self.get_topology_tree())

    def get_topology_pretty(self):
        # XML not in proper format: need to convert to lxml, then pretty-print
        return etree.tostring(etree.fromstring(self.get_topology()), pretty_print=True)

    ##########
    # Helpers
    ##########

    def __get_timestamp(self):
        # Return integer part as a string
        return str(int(time.time()))

    def __add_general_info(self):
        topo = ET.SubElement(self.topology_list, "topology")
        # Milliseconds in UTC format
        # TODO Save last update time on the physical topology (ListResources to RMs)
        topo.attrib["last_update_time"] = self.__get_timestamp()
        topo.attrib["type"] = "physical"
        # TODO Retrieve from config OR from slice!
        # TODO Filter topology based on this!
        topo.attrib["name"] = "urn_of_domain"
        # Set topology tag as root node for subsequent operations
        self.topology = topo

    def __add_generic_node(self, parent_tag, node, node_type):
        n = ET.SubElement(parent_tag, "node") 
        n.attrib["id"] = node.get("component_id")
        n.attrib["type"] = node_type
        # Generate management section for node
        n = self.__add_management_section(n)
        return n

    def __add_management_section(self, parent_node):
        management = ET.SubElement(parent_node, "management")
        # TODO Set management information for resources in another table/collection
        # TODO Query database for management information per resource
        # TODO Fill with retrieved information as needed
        # TODO Identify and update must/optional tags/attributes
#        resource_management_info = db_sync_manager.get_management_info(
#                                        component_id=parent_node.get("component_id"))
        management.attrib["type"] = "snmp"
        address = ET.SubElement(management, "address")
        address.text = "102.168.2.1"
        port = ET.SubElement(management, "port")
        port.text = "161"
        auth_id = ET.SubElement(management, "auth_id")
        auth_id.text = "public"
        auth_pass = ET.SubElement(management, "auth_pass")
        auth_pass.text = ""
        return parent_node

    def __add_generic_link(self, link):
        logger.debug("com-links=%s" % (link,))
        l = ET.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.attrib["type"] = link.get("link_type", "")
        if not l.attrib["type"]:
            l.attrib["type"] = "lan"
        # TODO Change structure of data
        links = link.get("links")
        for link_i in links:
            # XXX May need to parse, leave only the switch DPID and/or server
            # Source
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("source_id")
            # Destination
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("dest_id")

    #################
    # C-RM resources
    #################

    def __add_com_info(self):
        # 1. Nodes
        # TODO Filter nodes by network/domain
        nodes = [ n for n in db_sync_manager.get_com_nodes() ]
        for node in nodes:
            logger.debug("com-node=%s" % (node,))
            n = self.__add_generic_node(self.topology, node, "server")
            # Output interfaces per server
            logger.debug("com-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = ET.SubElement(n, "interface")
                # NOTE this is extending the "interface" URN
                interface.attrib["id"] = "%s+interface+%s" % (n.attrib["id"], iface)

        # 2. Links
        # TODO Filter links by network/domain
        links = [ l for l in db_sync_manager.get_com_links() ]
        logger.debug("com-links=%s" % (links,))
        for link in links:
            self.__add_generic_link(link)

    ###################
    # SDN-RM resources
    ###################

    def __add_sdn_info(self):
        # TODO Filter datapaths by network/domain
        datapaths = [ d for d in db_sync_manager.get_sdn_datapaths() ]
        for dp in datapaths:
            logger.debug("sdn-datapath=%s" % (dp,))
            switch = self.__add_generic_node(self.topology, dp, "switch")
            for p in dp.get("ports"):
                iface = ET.SubElement(switch, "interface")
                #iface.attrib["id"] = p.get("name")
                iface.attrib["id"] = "%s_%s" % (switch.attrib["id"], p.get("num"))
                port = ET.SubElement(iface, "port")
                port.attrib["num"] = p.get("num")

        # TODO Filter links by network/domain
        (sdn_links, fed_links) = [ l for l in db_sync_manager.get_sdn_links() ]
        for sdnl in sdn_links:
            logger.debug("sdn-link=%s" % (sdnl,))

        for fedl in fed_links:
            logger.debug("fed-link=%s" % (fedl,))

    ##################
    # TN-RM resources
    ##################

    def __add_tn_info(self):
        pass

    ##################
    # SE-RM resources
    ##################

    def __add_se_info(self):
        pass

