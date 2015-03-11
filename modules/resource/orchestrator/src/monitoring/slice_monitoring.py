from db.db_manager import db_sync_manager
from monitoring.base_monitoring import BaseMonitoring
from core.config import ConfParser
import requests
import time

import core
from lxml import etree
import xml.etree.ElementTree as ET

logger = core.log.getLogger("monitoring-slice")


class SliceMonitoring(BaseMonitoring):
    """
    Periodically communicates slice topology to the MS.
    Send monitoring info to MS after any GENIv3 provision & delete methods.
    """

    def __init__(self):
        super(SliceMonitoring, self).__init__()
        ms = ConfParser("ro.conf").get("monitoring")
        self.__ms_url = "%s://%s:%s%s" %\
            (ms.get("protocol"), ms.get("address"),
             ms.get("port"), ms.get("endpoint"))
        self.__topologies = etree.Element("topology_list")
        self.__stored = {}

    def __get_topologies(self):
        return etree.tostring(self.__topologies, pretty_print=True)

    def __add_snmp_management(self, tag, address,
                              port_num="161", auth_string="community"):
        manag = etree.SubElement(tag, "management", type="snmp")

        addr = etree.SubElement(manag, "address")
        addr.text = address
        port = etree.SubElement(manag, "port")
        port.text = port_num
        auth = etree.SubElement(manag, "auth")
        auth.text = auth_string

    def add_topology(self, slice_urn, client_urn=None):
        owner_name = client_urn if client_urn else "not_certified_user"
        topology = etree.SubElement(
            self.__topologies, "topology", type="slice",
            last_update_time=str(time.time()), name=slice_urn,
            owner=owner_name)
        # store the currect slice topology identifier
        self.__stored[slice_urn] = topology

    def add_c_resources(self, slice_urn, nodes, slivers):
        if slice_urn in self.__stored:
            logger.debug("Nodes(%d)=%s, Slivers(%d)=%s" %
                         (len(nodes), nodes, len(slivers), slivers))
            topology = self.__stored.get(slice_urn)
            for n in nodes:
                node_ = etree.SubElement(
                    topology, "node", id=n.get('component_id'), type="server")

                inner_node_ = etree.SubElement(
                    node_, "node", id=n.get('sliver_id'),
                    type=n.get('sliver_type_name'))

                if len(n.get('services')) > 0:
                    self.__add_snmp_management(
                        inner_node_,
                        n.get('services')[0].get('login').get('hostname'))
        else:
            logger.error("Unable to find Topology info from %s!" % slice_urn)

    def add_sdn_resources(self, slice_urn, nodes, slivers):
        # We cannot use information extracted from the manifest here!
        # We can look into the db-table containing the requested dpids
        # and matches.
        if slice_urn in self.__stored:
            logger.debug("Nodes(%d)=%s, Slivers(%d)=%s" %
                         (len(nodes), nodes, len(slivers), slivers))
        else:
            logger.error("Unable to find Topology info from %s!" % slice_urn)

    def send(self):
        try:
            logger.info("Send slice-monitoring info to %s: %s" %
                        (self.__ms_url, self.__get_topologies(),))

            hs = {'content-type': "application/xml"}
            r = requests.post(url=self.__ms_url, headers=hs,
                              data=self.__get_topologies())
            logger.info("Response=%s" % (r.text,))

        except Exception as e:
            logger.error("Unable to send slice-monitoring info to %s: %s" %
                         (self.__ms_url, e,))

    def retrieve_topology(self, peer):
        # General information
        self.__add_general_info()
        # COM resources
        self._add_com_info()
        # SDN resources
        self._add_sdn_info()
        # TN resources
        self._add_tn_info()
        # SE resources
        self._add_se_info()

    def send_topology(self, monitoring_server):
        logger.debug("Configured peers=%d" % (len(self.peers)))
        for peer in self.peers:
            # Looks for referred domain through peer ID; retrieve
            # URN and last update
            filter_params = {"_ref_peer": peer.get("_id"), }
            domain_peer = db_sync_manager.get_domain_info(filter_params)
            self.domain_urn = domain_peer.get("domain_urn")

            physical_topology = db_sync_manager.get_physical_info_from_domain(
                domain_peer.get("_id"))
            self.domain_last_update = physical_topology.get("last_update")
            logger.debug("Peer=%s, domain=%s" % (peer, self.domain_urn,))

            # Retrieve topology per peer
            self.retrieve_topology(peer)

        # Send topology after all peers are completed
        self._send(self.get_topology(), monitoring_server)
        logger.debug("Resulting RSpec=%s" % self.get_topology_pretty())

    ##########
    # Helpers
    ##########

    def __add_general_info(self):
        topo = ET.SubElement(self.topology_list, "topology")
        # Milliseconds in UTC format
        topo.attrib["last_update_time"] = self.domain_last_update
        topo.attrib["type"] = "slice"
        # TODO Retrieve from config OR from slice!
        # TODO Filter topology based on this!
        topo.attrib["name"] = "urn_of_slice"
        # TODO Retrieve owner from credentials
        topo.attrib["owner"] = "owner_of_slice"
        # Set topology tag as root node for subsequent operations
        self.topology = topo
