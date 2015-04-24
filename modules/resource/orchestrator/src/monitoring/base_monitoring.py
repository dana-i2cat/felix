from db.db_manager import db_sync_manager
from core.config import ConfParser
from core.organisations import AllowedOrganisations
from extensions.sfa.util.xrn import hrn_to_urn, urn_to_hrn
from lxml import etree

import ast
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
        ## Operation mode
        self.config = ConfParser("ro.conf")
        master_ro = self.config.get("master_ro")
        self.mro_enabled = ast.literal_eval(master_ro.get("mro_enabled"))
        ## Dictionaries
        self.felix_organisations = AllowedOrganisations.get_organisations_type()
        self.software_stacks = {
                                "ofelia": "ocf",
                                "felix": "fms",
                                }
        self.urn_type_resources = {
                                "crm": "vtam",
                                "sdnrm": "openflow",
                                "serm": "se",
                                "tnrm": "tn",
                                }
        self.urn_type_resources_variations = {
                                "crm": ["vtam"],
                                "sdnrm": ["openflow", "ofam"],
                                "serm": ["se"],
                                "tnrm": ["tn", "NSI"],
                                }
        self.management_type_resources = {
                                "crm": "server",
                                "sdnrm": "switch",
                                "serm": "se",
                                }
        self.peers_by_domain = {}
        self.__group_peers_by_domain()
        ## Configurations
        # CRM config
        self.config_crm = core.config.JSONParser("crm.json")
        self.crm_mgmt_info = self.config_crm.get("device_management_info")
        # SDNRM config
        self.config_sdnrm = core.config.JSONParser("sdnrm.json")
        self.sdnrm_mgmt_info = self.config_sdnrm.get("device_management_info")
        # SERM config
        self.config_serm = core.config.JSONParser("serm.json")
        self.serm_mgmt_info = self.config_serm.get("device_management_info")

    def __group_peers_by_domain(self):
        for peer in self.peers:
            filter_params = {"_ref_peer": peer.get("_id"),}
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            peer_domain_urn = domain_peer.get("domain_urn")
            authority = self._get_authority_from_urn(peer_domain_urn)
            if not self.peers_by_domain.get(authority):
                self.peers_by_domain[authority] = []
            self.peers_by_domain[authority].append(peer_domain_urn)

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


    ##########################
    # Set and return topology
    ##########################

    def set_topology_tree(self, topology_list_tree):
        # Return whole list of topologies
        try:
            # If the following line works, 'topology_list_tree' is a proper xml tree
            topology_list_proper = ET.tostring(self.get_topology_tree())
            self.topology_list = topology_list_tree
        except:
            pass
            
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

    def _get_authority_from_urn(self, urn):              
        authority = ""
        hrn, hrn_type = urn_to_hrn(urn)
        # Remove leaf (the component_manager part)
        hrn_list = hrn.split(".")
        hrn = ".".join(hrn_list[:-1])
        for hrn_element in hrn_list:
            if hrn_element in self.felix_organisations:
                authority = hrn_element
                break
        return authority
    
    def _update_topology_name(self):
        filter_string = "[@last_update_time='%s']" % str(self.domain_last_update)
        filtered_nodes = self.get_topology_tree().xpath("//topology%s" % filter_string)
        # There should only be one
        filtered_nodes[0].set("name", str(self.domain_urn))
        self.get_topology_tree().xpath("//topology%s" % filter_string)[0].set("name", str(self.domain_urn))
    
    def _remove_empty_topologies(self, filter_name=None, filter_update_time=None):
        filter_string = ""
        if filter_name:
            filter_string += "[@name='%s']" % str(filter_name)
        if filter_update_time:
            filter_string += "[@last_update_time='%s']" % str(filter_update_time)
        topology_tree = etree.fromstring(self.get_topology())
        filtered_nodes = topology_tree.xpath("//topology%s" % filter_string)
        for filtered_node in filtered_nodes:
            # Remove any node whose length is 0 (=> no content inside)
            if list(filtered_node) == 0:
                filtered_node.get_parent().remove(filtered_node)
        
    def _get_management_data_devices(self, parent_node):
        configuration_data = {}
        if self.urn_type_resources.get("crm") in parent_node.attrib["id"]:
            configuration_data = self.crm_mgmt_info
        elif self.urn_type_resources.get("sdnrm") in parent_node.attrib["id"]:
            configuration_data = self.sdnrm_mgmt_info
        elif self.urn_type_resources.get("serm") in parent_node.attrib["id"]:
            configuration_data = self.serm_mgmt_info
        return configuration_data

    def _add_management_section(self, parent_node):
        management = ET.Element("management")
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
            configuration_data = self._get_management_data_devices(parent_node)
            address.text = configuration_data.get(parent_node.attrib["id"]).get("ip")
            port.text = configuration_data.get(parent_node.attrib["id"]).get("port")
            auth_id.text = configuration_data.get(parent_node.attrib["id"]).get("snmp").get("id")
            auth_pass.text = configuration_data.get(parent_node.attrib["id"]).get("snmp").get("password")
        except Exception as e:
            logger.warning("Physical monitoring. Cannot add management data on %s. Details: %s" % (etree.tostring(parent_node), e))
        return management

    def _add_generic_node(self, parent_tag, node, node_type):
        n = ET.SubElement(parent_tag, "node")
        n.attrib["id"] = node.get("component_id")
        n.attrib["type"] = node_type
        # Generate management section for node
        # This is only active for normal RO operation (MRO should
        # probably not send this information to MMS)
        # XXX In case it should, MRO would store the full topology_list
        # from each RO and send them to MMS
        if not self.mro_enabled:
            if node_type in self.management_type_resources.values():
                try:
                    management = self._add_management_section(n)
                    n.append(management)
                except Exception as e:
                    logger.warning("Physical topology - Cannot add management section. Details: %s" % e)
        return n

    def _translate_link_types(self):
        topology_tree = etree.fromstring(self.get_topology())    
        filtered_links = topology_tree.xpath("//link")
        for filtered_link in filtered_links:
            if filtered_link.get("link_type"):
                filtered_link.set("link_type", self._translate_link_type(filtered_link))
            elif filtered_link.get("type"):
                filtered_link.set("type", self._translate_link_type(filtered_link))
        self.set_topology_tree(topology_tree)
    
    def _translate_link_type(self, link):
        # TODO - IMPORTANT FOR MS TO PARSE PROPERLY:
        #   Add others as needed in the future!
        default_type = "lan"
        
        ms_link_type_lan = "lan"
        ms_link_type_static_link = "static_link"
        ms_link_type_vlan_trans = "vlan_translation"
        link_type_translation = {
            "l2" : ms_link_type_lan,
            "l2 link": ms_link_type_lan,
            #"urn:felix+static_link": ms_link_type_static_link,
            "urn:felix+static_link": ms_link_type_lan,
#            "urn:felix+vlan_trans": ms_link_type_vlan_trans,
            "urn:felix+vlan_trans": ms_link_type_lan,
        }
        # Tries to get some attributes
        link_type = link.get("link_type", "")
        if not link_type:
            link_type = link.get("type", "")
        # Otherwise it uses a default value
        if not link_type:
            link_type = default_type
        else:
            link_type = link_type_translation.get(link_type.lower(), default_type)
        return link_type


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
            self._add_com_link(link)

    def _add_com_link(self, link):
        logger.debug("com-links=%s" % (link,))
        l = ET.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.attrib["type"] = self._translate_link_type(link)
        # TODO Change structure of data
        links = link.get("links")
        for link_i in links:
            # Source
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("source_id")
            # Destination
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link_i.get("dest_id")


    ###################
    # SDN-RM resources
    ###################

    def _add_sdn_info(self):
        # 1. Nodes
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
        # 2. Links
        (sdn_links, fed_links) = [ l for l in db_sync_manager.get_sdn_links_by_domain(self.domain_urn) ]
        for sdn_link in sdn_links:
            logger.debug("sdn-link=%s" % (sdn_link,))
            self._add_sdn_link(sdn_link)
        for sdn_fed_link in fed_links:
            logger.debug("fed-sdn-link=%s" % (sdn_fed_link,))

    def _add_sdn_link(self, link):
        l = ET.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.attrib["type"] = self._translate_link_type(link)
#        links = link.get("dpids")
#        for link in links:
#            # Source
#            iface = ET.SubElement(l, "interface_ref")
#            iface.attrib["client_id"] = link.get("component_id")

        # Parse the component_id to get URN of SDN and the port per interface
        component_id = link.get("component_id")
        tmp_urn_split = component_id.split("+link+")
        auth_urn = tmp_urn_split[0]
        sdn_datapath_urn = tmp_urn_split[0] + "+datapath+"
        try:
            # Parse and recompose back datapath URNs
            switch_src = sdn_datapath_urn + "_".join(tmp_urn_split[1].split("_")[:2])
            iface = ET.SubElement(l, "interface_ref")
#            iface.attrib["client_id"] = switch_src.split("_")[0]
            iface.attrib["client_id"] = switch_src
#            port = ET.SubElement(interface, "port")
#            port.attrib["num"] = switch_src.split("_")[1]

            switch_dst = sdn_datapath_urn + "_".join(tmp_urn_split[1].split("_")[2:4])
            iface = ET.SubElement(l, "interface_ref")
#            iface.attrib["client_id"] = switch_dst.split("_")[0]
            iface.attrib["client_id"] = switch_dst
        except Exception as e:
            logger.warning("Physical topology - Cannot add SE interface %s. Details: %s" % (component_id,e))


    ##################
    # TN-RM resources
    ##################

    def _add_tn_info(self):
        # 1. Nodes
        nodes = [ d for d in db_sync_manager.get_tn_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            logger.debug("tn-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "tn")
            # Output interfaces per node
            logger.debug("tn-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = ET.SubElement(n, "interface")
                interface.attrib["id"] = iface.get("component_id")
        # 2. Links
        links = [ l for l in db_sync_manager.get_tn_links_by_domain(self.domain_urn) ]


    ##################
    # SE-RM resources
    ##################

    def _add_se_info(self):
        # 1. Nodes
        nodes = [ d for d in db_sync_manager.get_se_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            logger.debug("se-node=%s" % (node,))
            n = self._add_generic_node(self.topology, node, "se")
            # Output interfaces per node
            logger.debug("se-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = ET.SubElement(n, "interface")
                # Parse the component_id to get URN of SE and the port per interface
                component_id = iface.get("component_id")
                try:
                    interface.attrib["id"] = component_id
#                    interface.attrib["id"] = component_id.split("_")[0]
                    port = ET.SubElement(interface, "port")
                    port.attrib["num"] = component_id.split("_")[1]
                except Exception as e:
                    logger.warning("Physical topology - Cannot add SE interface %s. Details: %s" % (component_id,e))
        # 2. Links
        links = [ l for l in db_sync_manager.get_se_links_by_domain(self.domain_urn) ]
        logger.debug("se-links=%s" % (links,))
        for link in links:
            logger.debug("se-links=%s" % (link,))
            self._add_se_link(link)

    def _add_se_link(self, link):
        l = ET.SubElement(self.topology, "link")
        # NOTE that this cannot be empty
        l.attrib["type"] = self._translate_link_type(link)
        links = link.get("interface_ref")
        for link in links:
            # SE link
            iface = ET.SubElement(l, "interface_ref")
            iface.attrib["client_id"] = link.get("component_id")
