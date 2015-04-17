from db.db_manager import db_sync_manager
from lxml import etree

import core
import re
import requests
import xml.etree.ElementTree as ET


logger = core.log.getLogger("monitoring-base")


class BaseMonitoring(object):
    """
    Base class for both physical and slice topology sent to the MS.
    """

    def __init__(self):
        super(BaseMonitoring, self).__init__()
        self.peers = [p for p in db_sync_manager.get_configured_peers()]
        self.domain_urn = ""
        self.domain_last_update = ""
        self.topology_list = ET.Element("topology_list")
        # CRM config
        self.config_crm = core.config.JSONParser("crm.json")
        self.crm_mgmt_info = self.config_crm.get("device_management_info")
        # SDNRM config
        self.config_sdnrm = core.config.JSONParser("sdnrm.json")
        self.sdnrm_mgmt_info = self.config_sdnrm.get("device_management_info")

    def _send(self, xml_data, peer=None):
        try:
            if not peer:
                peer = self.monitoring_system

            url = "%s:%s/%s" % (peer.get("address"),
                                     peer.get("port"), peer.get("endpoint"))
            # Post-process URL to remove N slashes in a row
            url = re.sub("/{2,}", "/", url)
            # And add protocol (with 2 slashes)
            url = "%s://%s" % (peer.get("protocol"), url)
            logger.info("url=%s" % (url,))
            logger.info("data=%s" % (xml_data,))

            # NOTE This may require certificates or BasicAuth at some point
            reply = requests.post(url=url,
                                 headers={"Content-Type": "application/xml"},
                                 data=xml_data).text
            logger.info("Reply=%s" % (reply,))

        except Exception as e:
            logger.error("Could not connect to %s. Exception: %s" % (url, e,))


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

    def _get_management_data_crm_sdnrm(self, parent_node):
        configuration_data = {}
        if "vtam" in parent_node.attrib["id"]:
            configuration_data = self.crm_mgmt_info
        elif "openflow" in parent_node.attrib["id"]:
            configuration_data = self.sdnrm_mgmt_info
        return configuration_data

    def _add_management_section(self, parent_node):
        management = ET.SubElement(parent_node, "management")
        # TODO Query database for management information per resource
        # TODO Identify and update must/optional tags/attributes
#        resource_management_info = db_sync_manager.get_management_info(
#                                        component_id=parent_node.get("component_id"))
        management.attrib["type"] = "snmp"
        address = ET.SubElement(management, "address")
        address.text = ""
        port = ET.SubElement(management, "port")
        port.text = ""
        auth_id = ET.SubElement(management, "auth_id")
        auth_id.text = "public"
        auth_pass = ET.SubElement(management, "auth_pass")
        auth_pass.text = ""
        try:
            configuration_data = self._get_management_data_crm_sdnrm(parent_node)
            address.text = configuration_data.get(parent_node.attrib["id"]).get("ip")
            port.text = configuration_data.get(parent_node.attrib["id"]).get("port")
            auth_id.text = configuration_data.get(parent_node.attrib["id"]).get("snmp").get("id")
            auth_pass.text = configuration_data.get(parent_node.attrib["id"]).get("snmp").get("password")
        except Exception as e:
            logger.warning("Physical monitoring. Cannot add management data. Details: %s" % (e))
        return parent_node

    def _add_generic_node(self, parent_tag, node, node_type):
        n = ET.SubElement(parent_tag, "node") 
        n.attrib["id"] = node.get("component_id")
        n.attrib["type"] = node_type
        # Generate management section for node
        n = self._add_management_section(n)
        return n

    def _add_generic_link(self, link):
        logger.debug("com-links=%s" % (link,))
        l = ET.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.attrib["type"] = link.get("link_type", "")
        if not l.attrib["type"]:
            l.attrib["type"] = "lan"
        # TODO Change structure of data
        links = link.get("links")
        for link_i in links:
            # Source
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("source_id")
            # Destination
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("dest_id")


    #################
    # C-RM resources
    #################

    def _add_com_info(self):
        # 1. Nodes
        nodes = [ n for n in db_sync_manager.get_com_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            logger.debug("com-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "server")
            # Output interfaces per server
            logger.debug("com-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = ET.SubElement(n, "interface")
                # NOTE this is extending the "interface" URN
                interface.attrib["id"] = "%s+interface+%s" % (n.attrib["id"], iface)

        # 2. Links
        links = [ l for l in db_sync_manager.get_com_links_by_domain(self.domain_urn) ]
        logger.debug("com-links=%s" % (links,))
        for link in links:
            self._add_generic_link(link)


    ###################
    # SDN-RM resources
    ###################

    def _add_sdn_info(self):
        datapaths = [ d for d in db_sync_manager.get_sdn_datapaths_by_domain(self.domain_urn) ]
        for dp in datapaths:
            logger.debug("sdn-datapath=%s" % (dp,))
            switch = self._add_generic_node(self.topology, dp, "switch")
            for p in dp.get("ports"):
                iface = ET.SubElement(switch, "interface")
                #iface.attrib["id"] = p.get("name")
                iface.attrib["id"] = "%s_%s" % (switch.attrib["id"], p.get("num"))
                port = ET.SubElement(iface, "port")
                port.attrib["num"] = p.get("num")

        (sdn_links, fed_links) = [ l for l in db_sync_manager.get_sdn_links_by_domain(self.domain_urn) ]
        for sdnl in sdn_links:
            logger.debug("sdn-link=%s" % (sdnl,))

        for fedl in fed_links:
            logger.debug("fed-link=%s" % (fedl,))


    ##################
    # TN-RM resources
    ##################

    def _add_tn_info(self):
        pass


    ##################
    # SE-RM resources
    ##################

    def _add_se_info(self):
        pass

