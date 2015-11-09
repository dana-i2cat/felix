from db.db_manager import db_sync_manager
from lxml import etree
from core.config import ConfParser
from core.utils.urns import URNUtils
from utils import MonitoringUtils
from utils_links import MonitoringUtilsLinks

import ast
import core
import re
import requests
import time

logger = core.log.getLogger("monitoring-base")


class BaseMonitoring(object):
    """
    Base class for both physical and slice topology sent to the MS.
    """

    def __init__(self):
        super(BaseMonitoring, self).__init__()
        self.peers = [p for p in db_sync_manager.get_configured_peers()]
        self.peers_info = [p for p in db_sync_manager.get_info_peers()]
        self.domain_urn = ""
        self.domain_last_update = ""
        self.topology_list = etree.Element("topology_list")
        self.topology = etree.SubElement(self.topology_list, "topology")
        ## Operation mode
        self.config = ConfParser("ro.conf")
        master_ro = self.config.get("master_ro")
        self.mro_enabled = ast.literal_eval(master_ro.get("mro_enabled"))
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
        self.monitoring_expected_nodes = {
                                "crm": "",
                                "sdnrm": "switch",
                                "serm": "se",
                                "tnrm": "tn",
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

    def _get_timestamp(self):
        # Return integer part as a string
        return str(int(time.time()))

    def __group_peers_by_domain(self):
        for peer in self.peers_info:
            filter_params = {"_id": peer.get("_id"),}
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            peer_domain_urn = domain_peer.get("domain_urn")
            authority = URNUtils.get_felix_authority_from_urn(peer_domain_urn)
            # If authority (domain name) does not exist yet, create
            if not self.peers_by_domain.get(authority):
                self.peers_by_domain[authority] = []
            # Extend list of peers with new one
            self.peers_by_domain[authority].append(peer_domain_urn)

            # Stores last_update_time for the physical topology
            # on a given domain
            try:
                last_update_time = self._get_timestamp()
                db_sync_manager.store_physical_info(peer_domain_urn,
                                                    last_update_time)
            except Exception as e:
                logger.error("Error storing last_update_time for phy-topology.")
                logger.error("Exception: %s" % e)

        # XXX: (M)MS assumes one TNRM per island
        # With this, (M)MS receives at least one TNRM per island
        type_resource_peer_tnrm = self.urn_type_resources_variations.get("tnrm")
        for peer in self.peers:
            filter_params = {"_ref_peer": peer.get("_id"),}
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            peer_domain_urn = domain_peer.get("domain_urn")
            peer_is_tnrm = any([rt in peer_domain_urn for rt in type_resource_peer_tnrm])
            # MRO: TNRM added at this level. Use information from peer to add it as a TNRM per domain
            if peer_is_tnrm:
                # Add the TNRM peer to each authority that does not have it yet
                for authority in self.peers_by_domain:
                    if peer_domain_urn not in self.peers_by_domain.get(authority):
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
            ## If the following line works, 'topology_list_tree' is a proper xml tree
            etree.tostring(topology_list_tree)
            self.topology_list = topology_list_tree
        except:
            pass

    def get_topology_tree(self):
        # Return whole list of topologies
        return self.topology_list

    def get_topology(self):
        if self.get_topology_tree() is not None:
            return etree.tostring(self.get_topology_tree())

    def get_topology_pretty(self):
        # XML not in proper format: need to convert to lxml, then pretty-print
        return etree.tostring(etree.fromstring(self.get_topology()), pretty_print=True)

    def flush_topology(self):
        # Create a new sub-element of the list of topologies
        self.topology = etree.SubElement(self.topology_list, "topology")

    def remove_empty_nodes(self):
        """Remove empty 'topology' nodes from the list/tree of topologies"""
        for node in self.topology_list.findall(".//topology"):
            if len(node.getchildren()) == 0:
                node.getparent().remove(node)


    ##########
    # Helpers
    ##########

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
        if self.urn_type_resources.get("crm") in parent_node.get("id"):
            configuration_data = self.crm_mgmt_info
        elif self.urn_type_resources.get("sdnrm") in parent_node.get("id"):
            configuration_data = self.sdnrm_mgmt_info
        elif self.urn_type_resources.get("serm") in parent_node.get("id"):
            configuration_data = self.serm_mgmt_info
        return configuration_data

    def _add_management_section(self, parent_node):
        management = etree.Element("management")
#        resource_management_info = db_sync_manager.get_management_info(
#                                        component_id=parent_node.get("component_id"))
        management.set("type", "snmp")
        address = etree.SubElement(management, "address")
        address.text = ""
        port = etree.SubElement(management, "port")
        port.text = ""
        auth_id = etree.SubElement(management, "auth_id")
        auth_id.text = "public"
        auth_pass = etree.SubElement(management, "auth_pass")
        auth_pass.text = ""
        try:
            configuration_data = self._get_management_data_devices(parent_node)
            if configuration_data is not None:
                # Possible mismatch between URN of *RM that is configured in the *rm.json config file
                # and the URN directly received from the RM. Issue a comprehensive warning here
                if not parent_node.get("id") in configuration_data.keys():
                    raise Exception("Mismatch between configuration device URN and received URN for URN='%s'. Please check the settings of your RMs under RO's configuration folder"
                                        % parent_node.get("id"))
                address.text = configuration_data.get(parent_node.get("id")).get("ip")
                port.text = configuration_data.get(parent_node.get("id")).get("port")
                auth_id.text = configuration_data.get(parent_node.get("id")).get("snmp").get("id")
                auth_pass.text = configuration_data.get(parent_node.get("id")).get("snmp").get("password")
        except Exception as e:
            logger.warning("Physical monitoring. Cannot add management data on '%s'. Details: %s" % (etree.tostring(parent_node), e))
        return management

    def _add_generic_node(self, parent_tag, node, node_type):
        n = etree.SubElement(parent_tag, "node")
        n.set("id", node.get("component_id"))
        n.set("type", node_type)
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


    #################
    # C-RM resources
    #################

    def _add_com_info(self, parent_node=None):
        # If no parent node passed, COM info is attached to root topology node
        if parent_node is None:
            parent_node = self.topology
        # 1. Nodes
        nodes = [ n for n in db_sync_manager.get_com_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "node", "server", node.get("component_id")):
                break
            logger.debug("com-node=%s" % (node,))
            # If no parent node passed, COM info is attached to root topology node
            if parent_node is None:
                parent_node = self.topology
            n = self._add_generic_node(parent_node, node, "server")
            # Output interfaces (avoid "*") per server
            node_ifaces = filter(lambda x: x!="*", node.get("interfaces"))
            logger.debug("com-node-interfaces=%s" % node_ifaces)
            for iface in node_ifaces:
                interface = etree.SubElement(n, "interface")
                # NOTE this is extending the "interface" URN
                interface.set("id", "%s+interface+%s" % (n.get("id"), iface))
        # 2. Links
        links = [ l for l in db_sync_manager.get_com_links_by_domain(self.domain_urn) ]
        logger.debug("com-links=%s" % (links,))
        for link in links:
            self._add_com_link(link, parent_node)

    def _add_com_link(self, link, parent_node=None):
        if parent_node is None:
            parent_node = self.topology
        logger.debug("com-links=%s" % (link,))
        #l = etree.SubElement(parent_node, "link")
        l = etree.Element("link")
        # NOTE that this cannot be empty
        l.set("type", MonitoringUtilsLinks._translate_link_type(link))
        link_id = ""
        links = link.get("links")
        link_exists = False
        for link_i in links:
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "link", "lan", [link_i.get("source_id"), link_i.get("dest_id")]):
                link_exists = True
                break
            # Modify link on-the-fly to add the DPID port as needed
            link_i = MonitoringUtilsLinks._set_dpid_port_from_link(link.get("component_id"), link_i)
            # Source
            iface_source = etree.SubElement(l, "interface_ref")
            iface_source.set("client_id", link_i.get("source_id"))
            # Destination
            iface_dest = etree.SubElement(l, "interface_ref")
            iface_dest.set("client_id", link_i.get("dest_id"))
            # - Prepare link ID for CRM-SDNRM link
            link_id = MonitoringUtilsLinks.get_id_for_link_crm_sdnrm(link_i)
        # Finally, add it as subelement
        if not link_exists:
            l.set("id", link_id)
            parent_node.append(l)


    ###################
    # SDN-RM resources
    ###################

    def _add_sdn_info(self, parent_node=None):
        # If no parent node passed, SDN info is attached to root topology node
        if parent_node is None:
            parent_node = self.topology
        # 1. Nodes
        datapaths = [ d for d in db_sync_manager.get_sdn_datapaths_by_domain(self.domain_urn) ]
        for dp in datapaths:
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "node", "switch", dp.get("component_id")):
                break
            logger.debug("sdn-datapath=%s" % (dp,))
            switch = self._add_generic_node(parent_node, dp, "switch")
            for p in dp.get("ports"):
                iface = etree.SubElement(switch, "interface")
                iface.set("id", "%s_%s" % (switch.get("id"), p.get("num")))
                port = etree.SubElement(iface, "port")
                port.set("num", p.get("num"))
        # 2. Links
        (sdn_links, fed_links) = [ l for l in db_sync_manager.get_sdn_links_by_domain(self.domain_urn) ]
        for sdn_link in sdn_links:
            logger.debug("sdn-link=%s" % (sdn_link,))
            self._add_sdn_link(sdn_link, parent_node)
        for sdn_fed_link in fed_links:
            logger.debug("fed-sdn-link=%s" % (sdn_fed_link,))

    def _add_sdn_link(self, link, parent_node=None):
        if parent_node is None:
            parent_node = self.topology
        auth1 = link.get("dpids")[0].get("component_manager_id").replace("authority+cm", "datapath")
        dpid1 = auth1 + "+" + link.get("dpids")[0].get("dpid") + "_" + link.get("ports")[0].get("port_num") 
        auth2 = link.get("dpids")[1].get("component_manager_id").replace("authority+cm", "datapath")
        dpid2 = auth2 + "+" + link.get("dpids")[1].get("dpid") + "_" + link.get("ports")[1].get("port_num") 
        if MonitoringUtils.check_existing_tag_in_topology(parent_node, "link", "lan", [dpid1, dpid2]):
            return
        l = etree.SubElement(parent_node, "link")
        # NOTE that this cannot be empty
        l.set("type", MonitoringUtilsLinks._translate_link_type(link))
        link_id = ""
        ports = link.get("ports")
        dpids = link.get("dpids")
        try:
            for dpid_port in zip(dpids, ports):
                iface = etree.SubElement(l, "interface_ref")
                dpid = dpid_port[0]["component_id"]
                port = dpid_port[1]["port_num"]
                iface.set("client_id", "%s_%s" % (dpid, port))
        except Exception as e:
            logger.warning("Physical topology - Cannot add SDN interface %s. Details: %s" % (link.get("component_id", "(unknown)"), e))
        try:
            # - Prepare link ID for SDNRM-SDNRM link
            link_id = MonitoringUtilsLinks.get_id_for_link_sdnrm_sdnrm(zip(dpids, ports))
            l.set("id", link_id)
        except Exception as e:
            logger.warning("Physical topology - Cannot add SDN link ID %s. Details: %s" % (link.get("component_id", "(unknown)"), e))



    ##################
    # TN-RM resources
    ##################

    def _add_tn_info(self, parent_node=None):
        # If no parent node passed, TN info is attached to root topology node
        if parent_node is None:
            parent_node = self.topology
        # 1. Nodes
        # XXX: (M)MS assumes one TNRM per island
        # This retrieves TN information from AIST instance
        # (providing MRO has TNRM as peer, or its information in its DB)
        felix_tn_urn = "urn:publicid:IDN+fms:aist:tnrm"
        nodes = [ d for d in db_sync_manager.get_tn_nodes_by_domain(felix_tn_urn) ]
#        nodes = [ d for d in db_sync_manager.get_tn_nodes_by_domain(self.domain_urn) ]
#        nodes = [ d for d in db_sync_manager.get_tn_nodes() ]
        for node in nodes:
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "node", "tn", node.get("component_id"), self.domain_urn):
                break
            logger.debug("tn-node=%s" % (node,))
            n = self._add_generic_node(parent_node, node, "tn")
            # Output interfaces per node
            logger.debug("tn-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = etree.SubElement(n, "interface")
                interface.set("id", iface.get("component_id"))
#        # 2. Links
#        links = [ l for l in db_sync_manager.get_tn_links_by_domain(self.domain_urn) ]


    ##################
    # SE-RM resources
    ##################

    def _add_se_info(self, parent_node=None):
        # If no parent node passed, SE info is attached to root topology node
        if parent_node is None:
            parent_node = self.topology
        # 1. Nodes
        nodes = [ d for d in db_sync_manager.get_se_nodes_by_domain(self.domain_urn) ]
        for node in nodes:
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "node", "se", node.get("component_id")):
                break
            logger.debug("se-node=%s" % (node,))
            n = self._add_generic_node(parent_node, node, "se")
            # Output interfaces per node
            logger.debug("se-node-interfaces=%s" % node.get("interfaces"))
            for iface in node.get("interfaces"):
                interface = etree.SubElement(n, "interface")
                # Parse the component_id to get URN of SE and the port per interface
                component_id = iface.get("component_id")
                try:
                    interface.set("id", component_id)
#                    interface.attrib["id"] = component_id.split("_")[0]
                    port = etree.SubElement(interface, "port")
                    port.set("num", component_id.split("_")[1])
                except Exception as e:
                    logger.warning("Physical topology - Cannot add SE interface %s. Details: %s" % (component_id,e))
        # 2. Links
        links = [ l for l in db_sync_manager.get_se_links_by_domain(self.domain_urn) ]
        logger.debug("se-links=%s" % (links,))
        for link in links:
            dpid1 = link.get("interface_ref")[0].get("component_id")
            dpid2 = link.get("interface_ref")[1].get("component_id")
            if MonitoringUtils.check_existing_tag_in_topology(parent_node, "link", "lan", [dpid1, dpid2]):
                break
            logger.debug("se-links=%s" % (link,))
            self._add_se_link(link)

    def _add_se_link(self, link):
        # Special case: links to be filtered in POST {(M)RO -> (M)MS}
        SE_FILTERED_LINKS = ["*"]
        interfaces_cid = [ i.get("component_id") for i in link.get("interface_ref") ]
        interface_cid_in_filter = [ f for f in SE_FILTERED_LINKS if f in interfaces_cid ]
        # Avoid reinserting existing link tags in the topology
        if MonitoringUtils.check_existing_tag_in_topology(self.topology, "link", "lan", link.get("component_id")):
            return
        if not interface_cid_in_filter:
            l = etree.SubElement(self.topology, "link")
            # NOTE that this cannot be empty
            l.set("type", MonitoringUtilsLinks._translate_link_type(link))
            link_id = ""
            links = link.get("interface_ref")
            for link in links:
                # SE link
                iface = etree.SubElement(l, "interface_ref")
                iface.set("client_id", link.get("component_id"))
            # - Prepare link ID for SERM-SDNRM link
            link_id = MonitoringUtilsLinks.get_id_for_link_serm_sdnrm_tnrm(links)
            l.set("id", link_id)

