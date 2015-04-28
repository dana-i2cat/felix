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

    PROVISIONED = "geni_provisioned"
    DELETED = "geni_unallocated"

    MS_LINK_TYPE = "lan"
    TN2TN_LINK_TYPE = "virtual-link"
    SDN2SDN_LINK_TYPE = "l2"

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

    def add_topology(self, slice_urn, status, client_urn=None):
        owner_name = client_urn if client_urn else "not_certified_user"
        # Convert the float number to an integer value as expected by MS!
        cm_time = int(round(time.time() * 1000))
        topology = etree.SubElement(
            self.__topologies, "topology", type="slice",
            last_update_time=str(cm_time), name=slice_urn,
            owner=owner_name, status=status)
        # store the currect slice topology identifier
        self.__stored[slice_urn] = topology

    def add_c_resources(self, slice_urn, nodes, slivers):
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("add_c_resources Nodes=%d" % (len(nodes),))
        for n in nodes:
            logger.debug("Node=%s" % (n,))

            node_ = etree.SubElement(
                topology, "node", id=n.get('component_id'), type="server")

            inner_node_ = etree.SubElement(
                node_, "node", id=n.get('sliver_id'),
                type=n.get('sliver_type_name'))

            if len(n.get('services')) > 0:
                self.__add_snmp_management(
                    inner_node_,
                    n.get('services')[0].get('login').get('hostname'))

    def __update_match_with_groups(self, match, groups):
        for mg in match.get('use_groups'):
            for g in groups:
                if g.get('name') == mg.get('name'):
                    match.get('dpids').extend(g.get('dpids'))
                    break

        logger.debug("Updated Match=%s" % (match,))

    def __add_packet_info(self, node_tag, packet_detail):
        m = etree.SubElement(node_tag, "match")
        vlans = packet_detail.get('dl_vlan').split(',', 1)
        if len(vlans) == 2:
            etree.SubElement(m, "vlan", start=vlans[0], end=vlans[1])
        else:
            etree.SubElement(m, "vlan", start=packet_detail.get('dl_vlan'),
                             end=packet_detail.get('dl_vlan'))

    def __create_link_id(self, datapath, portnumber):
        return datapath + "_" + str(portnumber)

    def __translate_link_type(self, ltype):
        # According to the MS definitions, we need to translate the link-type
        # to "lan" for all the different resources types (for now)
        logger.debug("Link-type: %s" % (ltype,))
        return self.MS_LINK_TYPE

    def __add_link_info(self, topology_tag, link_type, ep_src, ep_dst):
        link_type = self.__translate_link_type(link_type)

        link_ = etree.SubElement(topology_tag, "link", type=link_type)
        etree.SubElement(link_, "interface_ref", client_id=ep_src)
        etree.SubElement(link_, "interface_ref", client_id=ep_dst)

    def __extend_link_ids(self, ids):
        ret = []
        for i in ids:
            tmp = list(ids)
            tmp.remove(i)
            for t in tmp:
                ret.append(i + "_" + t)
        return ret

    def add_sdn_resources(self, slice_urn, nodes, slivers):
        # We cannot use information extracted from the manifest here!
        # We can look into the db-table containing the requested dpids
        # and matches.
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)
        groups, matches = db_sync_manager.get_slice_sdn(slice_urn)

        link_ids = []

        # Nodes info
        logger.debug("add_sdn_resources Groups(%d)=%s" % (len(groups), groups))
        logger.debug("add_sdn_resources Matches=%d" % (len(matches),))
        for m in matches:
            logger.debug("Match=%s" % (m,))
            self.__update_match_with_groups(m, groups)

            for dpid in m.get('dpids'):
                logger.debug("Dpid=%s" % (dpid,))

                node_ = etree.SubElement(
                    topology, "node", id=dpid.get('component_id'),
                    type="switch")

                for p in dpid.get('ports'):
                    ifid = dpid.get('component_id') + "_" + str(p.get('num'))
                    if_ = etree.SubElement(node_, "interface", id=ifid)

                    etree.SubElement(if_, "port", num=str(p.get('num')))

                    link_ids.append(
                        self.__create_link_id(dpid.get('dpid'), p.get('num')))

                self.__add_packet_info(node_, m.get('packet'))

        logger.info("add_sdn_resources Link identifiers(%d)=%s" %
                    (len(link_ids), link_ids,))
        # C-SDN link info
        for l in link_ids:
            com_link = db_sync_manager.get_com_link_by_sdnkey(l)
            if com_link:
                logger.debug("COM link=%s" % (com_link,))
                for eps in com_link.get('links'):
                    self.__add_link_info(
                        topology, com_link.get('link_type'),
                        eps.get('source_id'), eps.get('dest_id'))

        # SDN-SDN link info
        ext_link_ids = self.__extend_link_ids(link_ids)
        logger.info("add_sdn_resources Extended link identifiers(%d)=%s" %
                    (len(ext_link_ids), ext_link_ids,))
        for l in ext_link_ids:
            sdn_link = db_sync_manager.get_sdn_link_by_sdnkey(l)
            if sdn_link:
                logger.debug("SDN link=%s" % (sdn_link,))
                if len(sdn_link.get('dpids')) == 2 and\
                   len(sdn_link.get('ports')) == 2:
                    ep1 = self.__create_link_id(
                        sdn_link.get('dpids')[0].get('component_id'),
                        sdn_link.get('ports')[0].get('port_num'))
                    ep2 = self.__create_link_id(
                        sdn_link.get('dpids')[1].get('component_id'),
                        sdn_link.get('ports')[1].get('port_num'))
                    self.__add_link_info(topology, self.SDN2SDN_LINK_TYPE,
                                         ep1, ep2)

    def __add_rest_management(self, tag, address, port_num, protocol,
                              endpoint="/metrics/list/"):
        manag = etree.SubElement(tag, "management", type="rest")

        addr = etree.SubElement(manag, "address")
        addr.text = address
        port = etree.SubElement(manag, "port")
        port.text = port_num
        proto = etree.SubElement(manag, "protocol")
        proto.text = protocol
        endp = etree.SubElement(manag, "endpoint")
        endp.text = endpoint

    def add_tn_resources(self, slice_urn, nodes, links, slivers, peer_info):
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("add_tn_resources Nodes=%d, PeerInfo=%s" %
                     (len(nodes), peer_info,))
        for n in nodes:
            logger.debug("Node=%s" % (n,))

            node_ = etree.SubElement(
                topology, "node", id=n.get('component_id'), type="tn")

            vlan_ids = set()
            for ifs in n.get('interfaces'):
                etree.SubElement(
                    node_, "interface", id=ifs.get('component_id'))
                for v in ifs.get('vlan'):
                    vlan_ids.add(v.get('tag'))

            logger.debug("Vlan-ids=%s" % vlan_ids)
            for vlan in vlan_ids:
                m_ = etree.SubElement(node_, "match")
                etree.SubElement(m_, "vlan", start=vlan, end=vlan)

            self.__add_rest_management(
                node_, peer_info.get('address'), peer_info.get('port'),
                peer_info.get('protocol'))

        logger.debug("add_tn_resources Links=%d" % (len(links),))
        for l in links:
            logger.debug("Link=%s" % (l,))

            for p in l.get('property'):
                self.__add_link_info(topology, self.TN2TN_LINK_TYPE,
                                     p.get('source_id'), p.get('dest_id'))

    def add_se_resources(self, slice_urn, nodes, links, slivers):
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("add_se_resources Nodes=%d" % (len(nodes),))
        for n in nodes:
            logger.debug("Node=%s" % (n,))

            node_ = etree.SubElement(
                topology, "node", id=n.get('component_id'), type="se")

            if n.get('host_name'):
                self.__add_snmp_management(node_, n.get('host_name'))

            vlan_ids = set()
            for ifs in n.get('interfaces'):
                etree.SubElement(
                    node_, "interface", id=ifs.get('component_id'))
                for v in ifs.get('vlan'):
                    vlan_ids.add(v.get('tag'))

            logger.debug("Vlan-ids=%s" % vlan_ids)
            for vlan in vlan_ids:
                m_ = etree.SubElement(node_, "match")
                etree.SubElement(m_, "vlan", start=vlan, end=vlan)

        logger.debug("add_se_resources Links=%d" % (len(links),))
        for l in links:
            logger.debug("Link=%s" % (l,))

            if len(l.get('interface_ref')) != 2:
                logger.warning("Unable to manage extra-list of info (%d)!" %
                               len(l.get('interface_ref')))
                continue

            self.__add_link_info(topology, l.get('link_type'),
                                 l.get('interface_ref')[0].get('component_id'),
                                 l.get('interface_ref')[1].get('component_id'))
            self.__add_link_info(topology, l.get('link_type'),
                                 l.get('interface_ref')[1].get('component_id'),
                                 l.get('interface_ref')[0].get('component_id'))

    def send(self):
        try:
            logger.info("Send slice-monitoring info to %s: %s" %
                        (self.__ms_url, self.__get_topologies(),))

            hs = {'content-type': "application/xml"}
            r = requests.post(url=self.__ms_url, headers=hs,
                              data=self.__get_topologies())
            logger.info("Response=%s, text=%s" % (r, r.text,))

        except Exception as e:
            logger.error("Unable to send slice-monitoring info to %s: %s" %
                         (self.__ms_url, e,))

    def serialize(self):
        return etree.tostring(self.__topologies)

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
        # retrieve slice info from db (the info are already formatted!)
        slices = db_sync_manager.get_slice_monitoring_info()
        logger.debug("Slices: %d" % (len(slices),))
        for s in slices:
            self.__topologies = etree.fromstring(s)
            self.send()

    def delete_slice_topology(self, slice_urn):
        logger.info("Slice URN: %s" % (slice_urn,))
        sinfo = db_sync_manager.get_slice_monitoring_from_urn(slice_urn)
        logger.debug("Monitoring Info: %s" % (sinfo,))

        if sinfo is not None:
            self.__topologies = etree.fromstring(sinfo)
            for t in self.__topologies.findall("topology"):
                t.attrib["status"] = self.DELETED
            self.send()

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
