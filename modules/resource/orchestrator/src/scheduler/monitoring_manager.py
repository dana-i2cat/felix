from core.config import ConfParser
from delegate.geni.v3.db_manager import db_sync_manager
from resource_detector import ResourceDetector

import core
import requests
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-manager")


class MonitoringManager(ResourceDetector):
    """
    Periodically communicates monitoring data to the MON system.
    """

    def __init__(self):
        super(MonitoringManager, self).__init__("monitoring")
        self.config = ConfParser("ro.conf")
        self.monitoring_section = self.config.get("monitoring")
        self.protocol = self.monitoring_section.get("protocol")
        self.address = self.monitoring_section.get("address")
        self.port = self.monitoring_section.get("port")
        self.endpoint = self.monitoring_section.get("endpoint")
        self.monitoring_system = {"protocol": self.protocol,
                                    "address": self.address,
                                    "address": self.address,
                                    "address": self.address
                                }

    def physical_info(self):
        self.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            self.debug("Peer=%s" % (peer,))

            root = ET.Element("topology")
            root.attrib["type"] = "physical"
            # General information
            self.__add_general_info(root)
            # COM resources
            self.__add_com_info(root)
            # SDN resources
            self.__add_sdn_info(root)
            # Send whole data
            self.__send(peer, root)

    def __send(self, xml_data, peer=self.monitoring_system):
        try:
            url = "%s://%s:%s/%s" % (peer.get("protocol"), peer.get("address"),
                                     peer.get("port"), peer.get("endpoint"))
            self.info("url=%s" % (url,))
            data = ET.tostring(xml_data)
            self.info("data=%s" % (data,))

            resp = requests.post(url=url,
                                 headers={"Content-Type": "application/xml"},
                                 data=data).text
            self.info("Resp=%s" % (resp,))

        except Exception as e:
            self.error("Exception: %s" % (e,))

    def __add_general_info(self, root):
        d = ET.SubElement(root, "domain")
        d.attrib["id"] = db_sync_manager.get_domain_id()

#  <node id="jgnx+server1.rise.jgnx.net" network_name="jgnx" type="server">
#    <display_name>server1.rise.jgnx.net</display_name>
#    <server_info>
#      <vm_id>sliceA+edge-node-2</vm_id>
#      <vm_id>sliceB+edge-node-1</vm_id>
#    </server_info>
#    <interface id="server1.rise.jgnx.net_eth1"/>
#  </node>
#
#  <link type="lan">
#    <interface_ref client_id="00:00:00:00:00:00:00:01_13" network_name="jgnx"/>
#    <interface_ref client_id="server1.rise.jgnx.net_eth1" network_name="jgnx"/>
#  </link>

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
            display = ET.SubElement(n, "display_name")
            display.text = node.get("component_manager_id")
            # TODO Set table for VirtualMachines per server
            server_info = ET.SubElement(n, "server_info")
            for vm in n.get("virtual_machines"):
                v = ET.SubElement(server_info, "vm_id")
                v.text = vm.get("component_id")
            # Output interfaces per server
            for iface in n.get("interfaces"):
                interface = ET.SubElement(n, "server_info")
                interface.attrib["id"] = "%s_%s" % (n.get("component_id"), iface)

            # { "_id" : ObjectId("546f627606e5c06fa8a6cd07"), "property" : [ 	{ 	"source_id" : "urn:publicid:IDN+ocf:i2cat:vtam:Rodoreda+interface+eth1", "dest_id" : "urn:publicid:IDN+ocf:ofam+datapath+00:10:00:00:00:00:00:03", 	"capacity" : "1024MB/s" } ], "routing_key" : ObjectId("546e24a406e5c01a4cfa10a3"), "component_id" : "urn:publicid:IDN+ocf:i2cat:vtam+Rodoreda+link+eth1-00:10:00:00:00:00:00:03", "link_type" : "", "component_name" : "urn:publicid:IDN+ocf:i2cat:vtam+Rodoreda+link+eth1-00:10:00:00:00:00:00:03" }

        # 2. Links
        links = db_sync_manager.get_com_links()
        for link in links:
            self.debug("com-links=%s" % (link,))
            l = ET.SubElement(root, "link")
            l.attrib["type"] = "lan"
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
