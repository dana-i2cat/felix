from core.config import ConfParser
from delegate.geni.v3.db_manager import db_sync_manager

import core
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-manager")


class PhysicalMonitoring():
    """
    Periodically communicates physical topology to the MS.
    """

    def __init__(self):
        self.peers = db_sync_manager.get_configured_peers()
        self.topology = ET.Element("topology")
        self.retrieve_topology()

    def retrieve_topology(self):
        self.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            self.debug("Peer=%s" % (peer,))
            # General information
            self.__add_general_info()
            # COM resources
            self.__add_com_info()
            # SDN resources
            self.__add_sdn_info()
            # TN resources
            self.__add_tn_info()
            # SE resources
            self.__add_se_info()

    def get_topology_tree(self):
        return self.topology

    def get_topology(self):
        return ET.tostring(self.get_topology_tree())

    def __add_general_info(self):
        self.topology.attrib["type"] = "physical"
        self.topology.attrib["last_update_time"] = "" # TODO Fill
        for peer in self.peers:
            n = ET.SubElement(self.topology, "network")
            n.attrib["name"] = db_sync_manager.get_domain_id()

    def __add_com_info(self, root):
        # 1. Nodes
        nodes = db_sync_manager.get_com_nodes()
        for node in nodes:
            self.debug("com-nodes=%s" % (node,))
            n = ET.SubElement(root, "node")
            n.attrib["id"] = node.get("component_id")
            # TODO Import urn_to_hrn, then extract authority
            n.attrib["network_name"] = node.get("component_manager_id")
            n.attrib["type"] = "server"
            #display = ET.SubElement(n, "display_name")
            #display.text = node.get("component_manager_id")
            # TODO Set table for VirtualMachines per server
            #server_info = ET.SubElement(n, "node")
            #for vm in n.get("virtual_machines"):
            #    v = ET.SubElement(server_info, "vm_id")
            #    v.text = vm.get("component_id")
            ## Output interfaces per server
            for iface in n.get("interfaces"):
                interface = ET.SubElement(n, "interface")
                interface.attrib["id"] = "%s_%s" % (n.get("component_id"), iface)

        # 2. Links
        links = db_sync_manager.get_com_links()
        for link in links:
            self.__add_generic_link(link)

    def __add_generic_link(link):
        self.debug("com-links=%s" % (link,))
        l = ET.SubElement(self.topology, "link")
        l.attrib["type"] = link.get("link_type")
        # TODO Change structure of data
        prop = link.get("links")
        for p in prop:
            iface = ET.SubElement(l, "interface_ref")
            # XXX May need to parse, leave only the switch DPID and/or server
            iface.attrib["client_id"] = l.get("component_id")
            l.attrib["network_name"] = l.get("component_id")

    def __add_sdn_info(self, root):
        datapaths = db_sync_manager.get_sdn_datapaths()
        for dp in datapaths:
            self.debug("sdn-datapath=%s" % (dp,))
            switch = ET.SubElement(root, "switch")
            switch.attrib["id"] = dp.get("dpid")
            for p in dp.get("ports"):
                intf = ET.SubElement(switch, "interface")
                intf.attrib["id"] = p.get("name")
                intf.attrib["number"] = p.get("num")

        (sdn_links, fed_links) = db_sync_manager.get_sdn_links()
        for sdnl in sdn_links:
            self.debug("sdn-link=%s" % (sdnl,))

        for fedl in fed_links:
            self.debug("fed-link=%s" % (fedl,))

