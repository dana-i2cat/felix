from db.db_manager import db_sync_manager
from monitoring.base_monitoring import BaseMonitoring
from core.config import ConfParser
from core.utils.urns import URNUtils
from utils import MonitoringUtils
from utils_links import MonitoringUtilsLinks

import requests
import time
import core
from lxml import etree

logger = core.log.getLogger("monitoring-slice")


class SliceMonitoring(BaseMonitoring):
    """
    Periodically communicates slice topology to the MS.
    Send monitoring info to MS after any GENIv3 provision & delete methods.
    """

    PROVISIONED = "geni_provisioned"
    DELETED = "geni_unallocated"

    MS_LINK_TYPE = "lan"
    SE_LINK_TYPE = "se"
    TN2TN_LINK_TYPE = "tn"
    SDN2SDN_LINK_TYPE = "l2"

    def __init__(self):
        super(SliceMonitoring, self).__init__()
        ms = ConfParser("ro.conf").get("monitoring")
        self.__ms_url = "%s://%s:%s%s" %\
            (ms.get("protocol"), ms.get("address"),
             ms.get("port"), ms.get("endpoint"))
        self.__topologies = etree.Element("topology_list")
        self.__stored = {}
        self.__mapping_c_interface = {}
        #self.__sdn_links = []
        self.__se_links = []
        self.__tn_links = []
        self.__hybrid_links = []

    def __get_topologies(self):
        """
        Returns a pretty version of the whole tree (list of topologies).
        @return topologies tree in a pretty format
        """
        return etree.tostring(self.__topologies, pretty_print=True)

    def __add_snmp_management(self, tag, address,
                              port_num="161", auth_string="community"):
        """
        Inserts a new node (subelement) inside an lxml.etree
        with access information to retrieve monitoring metrics.
        Currently set to retrieve data through SNMP.

        @param tag tree node from where to insert the management section
        @param address IP adress used to access a device
        @param port_num port number used to access a device
        @param auth_string identifier, token, password... used to access
                           a device
        """
        manage = etree.SubElement(tag, "management", type="snmp")
        addr = etree.SubElement(manage, "address")
        addr.text = address
        port = etree.SubElement(manage, "port")
        port.text = port_num
        auth = etree.SubElement(manage, "auth")
        auth.text = auth_string

    def __check_ids_same_domain(self, src_id, dst_id):
        auth_src = URNUtils.get_felix_authority_from_urn(src_id)
        auth_dst = URNUtils.get_felix_authority_from_urn(dst_id)
        return auth_src == auth_dst

    def add_topology(self, slice_urn, status, client_urn=None):
        """
        Inserts a new node (subelement) inside an lxml.etree
        with a topology for a given domain or island.

        @param slice_urn URN identifier of a given slice
        @param status Status of the resources, as in GENI
                      Possible values: {geni_allocated|geni_unallocated|
                                        geni_provisioned}
        @param client_urn URN identifier of the client originating the request
        """
        owner_name = client_urn if client_urn else "not_certified_user"
        # Convert the float number to an integer value as expected by MS!
        cm_time = int(round(time.time()))
        topology = etree.SubElement(
            self.__topologies, "topology", type="slice",
            last_update_time=str(cm_time), name=slice_urn,
            owner=owner_name, status=status)
        # Store the currect slice topology identifier
        self.__stored[slice_urn] = topology

    def add_c_resources(self, slice_urn, nodes):
        """
        Inserts one or more nodes with CRM resources information.

        @param slice_urn URN identifier of a given slice
        @param nodes Structure containing a list of CRM nodes and
                     its attributes
        """
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("add_c_resources Nodes=%d" % (len(nodes),))
        for n in nodes:
            logger.debug("Node=%s" % (n,))

            node_ = etree.SubElement(
                topology, "node", id=n.get("component_id"), type="server")

            inner_node_ = etree.SubElement(
                node_, "node", id=n.get("sliver_id"),
                type=n.get("sliver_type_name").lower())

            # Add the interface identifier of the server node here!
            # In the future, it will be the vlan-tagged interface of the
            # virtual machine (much more sense)
            nodekey = n.get("component_id").replace("+node+", ":")
            logger.debug("Node key=%s" % (nodekey,))
            interfaces = db_sync_manager.get_com_interface_by_nodekey(nodekey)
            logger.info("Stored COM interfaces=%s" % (interfaces,))
            for i in interfaces:
                if_index = i.rfind("interface")
                if_name = n.get("sliver_id") + "+" + i[if_index:len(i)]
                etree.SubElement(inner_node_, "interface", id=if_name)
                self.__mapping_c_interface[i] = if_name

            if len(n.get("services")) > 0:
                self.__add_snmp_management(
                    inner_node_,
                    n.get("services")[0].get("login").get("hostname"))

    def __update_match_with_groups(self, match, groups):
        for mg in match.get("use_groups"):
            for g in groups:
                if g.get("name") == mg.get("name"):
                    match.get("dpids").extend(g.get("dpids"))
                    break

        logger.debug("Updated Match=%s" % (match,))

    def __add_packet_info(self, node_tag, packet_detail):
        m = etree.SubElement(node_tag, "match")
        vlans = packet_detail.get("dl_vlan")
        if vlans is not None:
            vlans = vlans.split(",", 1)
            if len(vlans) == 2:
                etree.SubElement(m, "vlan", start=vlans[0], end=vlans[1])
            else:
                etree.SubElement(m, "vlan", start=packet_detail.get("dl_vlan"),
                                 end=packet_detail.get("dl_vlan"))

    def __create_link_id(self, datapath, portnumber):
        return datapath + "_" + str(portnumber)

    def __translate_link_type(self, ltype):
        # According to the MS definitions, we need to translate the link-type
        # to "lan" for all the different resources types (for now)
        # except for TN-links, they have to be "tn"
        logger.debug("Link-type: %s" % (ltype,))
        if ltype == self.TN2TN_LINK_TYPE:
            return self.TN2TN_LINK_TYPE
        return self.MS_LINK_TYPE

    def __add_link_info(self, topology_tag, ep_src, ep_dst, link_type=None):
        # No link_type provided => interfaces appended directly under given tag
        root = topology_tag
        if link_type is not None:
            link_type = self.__translate_link_type(link_type)
            link_ = etree.Element("link")
            link_.set("type", link_type)
            root = link_
        if MonitoringUtils.check_existing_tag_in_topology(root, "link", link_type, [ep_src, ep_dst]):
            return
        if link_type is not None:
            topology_tag.append(root)
        etree.SubElement(root, "interface_ref", client_id=ep_src)
        etree.SubElement(root, "interface_ref", client_id=ep_dst)

    def __extend_link_ids(self, ids):
        ret = []
        for i in ids:
            tmp = list(ids)
            tmp.remove(i)
            for t in tmp:
                ret.append(i + "_" + t)
        return ret

    def __get_eps_ids(self, source_id, dest_id):
        eps_src_id, eps_dst_id = source_id, dest_id

        if self.__mapping_c_interface.get(source_id) is not None:
            eps_src_id = self.__mapping_c_interface.get(source_id)
        if self.__mapping_c_interface.get(dest_id) is not None:
            eps_dst_id = self.__mapping_c_interface.get(dest_id)

        return eps_src_id, eps_dst_id

    def add_sdn_resources(self, slice_urn, nodes):
        """
        Inserts one or more nodes with SDNRM resources information.

        @param slice_urn URN identifier of a given slice
        @param nodes Structure containing a list of SDNRM nodes and
                     its attributes
        """
        # Cannot use information extracted from the manifest here!
        # Look into the db-table containing the requested dpids and matches.
        if slice_urn not in self.__stored:
            logger.error("Slice monitoring: unable to find topology " +
                         "info from %s!" % slice_urn)
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

            ## TODO Check db.topology.slice (maybe some information stored?)
            for dpid in m.get("dpids"):
                if MonitoringUtils.check_existing_tag_in_topology(topology, "node", "switch", dpid.get("component_id")):
                    break
                logger.debug("Dpid=%s" % (dpid,))

                node_ = etree.SubElement(
                    topology, "node", id=dpid.get("component_id"),
                    type="switch")

                for p in dpid.get("ports"):
                    ifid = dpid.get("component_id") + "_" + str(p.get("num"))
                    if_ = etree.SubElement(node_, "interface", id=ifid)

                    etree.SubElement(if_, "port", num=str(p.get("num")))

                    link_ids.append(
                        self.__create_link_id(dpid.get("dpid"), p.get("num")))

                self.__add_packet_info(node_, m.get("packet"))

        logger.info("add_sdn_resources Link identifiers(%d)=%s" %
                    (len(link_ids), link_ids,))
        # C-SDN link info
        for l in link_ids:
            com_link = db_sync_manager.get_com_link_by_sdnkey(l)
            if com_link:
                logger.debug("COM link=%s" % (com_link,))
                for eps in com_link.get("links"):
                    if MonitoringUtils.check_existing_tag_in_topology(topology, "link",\
                        self.MS_LINK_TYPE, [eps.get("source_id"), eps.get("dest_id")]):
                        break

                    # Modify link on-the-fly to add the DPID port as needed
                    eps = MonitoringUtilsLinks._set_dpid_port_from_link(
                        com_link.get("component_id"), eps)

                    eps_src_id, eps_dst_id = self.__get_eps_ids(
                        eps.get("source_id"), eps.get("dest_id"))

                    logger.info("eps_src_id=%s, eps_dst_id=%s" %
                                (eps_src_id, eps_dst_id,))
                    self.__add_link_info(topology, eps_src_id, eps_dst_id, com_link.get("link_type"))

        # SDN-SDN link info
        ext_link_ids = self.__extend_link_ids(link_ids)
        logger.info("add_sdn_resources Extended link identifiers(%d)=%s" %
                    (len(ext_link_ids), ext_link_ids,))
        for l in ext_link_ids:
            sdn_link = db_sync_manager.get_sdn_link_by_sdnkey(l)
            if sdn_link:
                logger.debug("SDN link=%s" % (sdn_link,))
                if len(sdn_link.get("dpids")) == 2 and\
                   len(sdn_link.get("ports")) == 2:
                    ep1 = self.__create_link_id(
                        sdn_link.get("dpids")[0].get("component_id"),
                        sdn_link.get("ports")[0].get("port_num"))
                    ep2 = self.__create_link_id(
                        sdn_link.get("dpids")[1].get("component_id").
                        sdn_link.get("ports")[1].get("port_num"))
                    # Local SDN-SDN links are not inserted under the nested link
#                    if self.__check_ids_same_domain(ep1, ep2):
                    self.__add_link_info(topology, ep1, ep2, self.SDN2SDN_LINK_TYPE)
#                    else:
#                        self.__sdn_links.append(
#                            {'id': sdn_link.get("component_id"),
#                             'source': ep1,
#                             'destination': ep2})
            else:
                logger.info("Slice monitoring: cannot find link that " +
                            "ends with %s" % l)

    def __add_rest_management(self, tag, address, port_num, protocol,
                              endpoint="/metrics/list/"):
        manage = etree.SubElement(tag, "management", type="rest")
        addr = etree.SubElement(manage, "address")
        addr.text = address
        port = etree.SubElement(manage, "port")
        port.text = port_num
        proto = etree.SubElement(manage, "protocol")
        proto.text = protocol
        endp = etree.SubElement(manage, "endpoint")
        endp.text = endpoint

    def add_tn_resources(self, slice_urn, nodes, links, peer_info):
        """
        Inserts one or more nodes with TNRM resources information.

        @param slice_urn URN identifier of a given slice
        @param nodes Structure containing a list of TNRM nodes and
                     its attributes
        @param links Structure containing a list of TNRM links and
                     its attributes
        @param peer_info Structure containing a number of specific attributes
                         of a given peer
        """
        if slice_urn not in self.__stored:
            logger.error("Slice monitoring: unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("add_tn_resources Nodes=%d, PeerInfo=%s" %
                     (len(nodes), peer_info,))
        # Iterate over the TN nodes to fetch its component ID, interface and associated VLAN tag
        for n in nodes:
            logger.debug("Node=%s" % (n,))

            node_ = etree.SubElement(
                topology, "node", id=n.get("component_id"), type=self.TN2TN_LINK_TYPE)

            for ifs in n.get("interfaces"):
                etree.SubElement(
                    node_, "interface", id=ifs.get("component_id"))
                vlan = ifs.get("vlan")[0].get("tag")
                m_ = etree.SubElement(node_, "match")
                etree.SubElement(m_, "vlan", start=vlan, end=vlan)

            self.__add_rest_management(
                node_, peer_info.get("address"), peer_info.get("port"),
                peer_info.get("protocol"))

        # MRO: TN links are transmitted at this layer
        if self.mro_enabled:
            logger.debug("add_tn_resources Links=%d" % (len(links),))
            for l in links:
                logger.debug("Link=%s" % (l,))
                # In order to avoid duplication in case of bidirectional links
                # we use the attributes of the first "property" here!
                if len(l.get("property")) >= 1:
                    p = l.get("property")[0]
                    #self.__add_link_info(topology, p.get("source_id"), p.get("dest_id"), self.TN2TN_LINK_TYPE)
                    # store the values for the virtual island-to-island link
                    self.__tn_links.append(
                        {'id': l.get("component_id"),
                         'source': p.get("source_id"),
                         'destination': p.get("dest_id")})

    def __add_se_external_link_info(self, topo, ifs):
        for i in ifs:
            logger.debug("Searching EXTERNAL-IF from %s" % (i,))
            extif = db_sync_manager.get_interface_ref_by_sekey(i)
            logger.info("External-interface %s" % (extif,))

            if extif is not None:
                # Adding SE-to-SDN or SE-to-TN link
#                self.__add_link_info(topo, i, extif, self.MS_LINK_TYPE)
                # store the values for the virtual island-to-island link
                self.__hybrid_links.append({'source': i, 'destination': extif})

#                if extif.count("ofam") == 1:
#                    # Adding "abstract" link
#                    self.__add_link_info(topo, extif, "*", self.MS_LINK_TYPE)

    def __add_se_port_from_interface(self, if_id, if_tag):
        index = if_id.rfind("_")
        if index != -1:
            etree.SubElement(if_tag, "port", num=if_id[index+1:len(if_id)])

    def add_se_resources(self, slice_urn, nodes, links):
        """
        Inserts one or more nodes with SERM resources information.

        @param slice_urn URN identifier of a given slice
        @param nodes Structure containing a list of SERM nodes and
                     its attributes
        @param links Structure containing a list of SERM links and
                     its attributes
        """
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)

        logger.debug("dd_se_resources Nodes=%d" % (len(nodes),))
        for n in nodes:
            logger.debug("Node=%s" % (n,))
            node_ = etree.SubElement(
                topology, "node", id=n.get("component_id"), type=self.SE_LINK_TYPE)

            if n.get("host_name"):
                self.__add_snmp_management(node_, n.get("host_name"))

            for ifs in n.get("interfaces"):
                interface_ = etree.SubElement(
                    node_, "interface", id=ifs.get("component_id"))
                # Try to extract port info from the component id!
                self.__add_se_port_from_interface(
                    ifs.get("component_id"), interface_)
                vlan = ifs.get("vlan")[0].get("tag")
                m_ = etree.SubElement(node_, "match")
                etree.SubElement(m_, "vlan", start=vlan, end=vlan)

        logger.debug("add_se_resources Links=%d" % (len(links),))
        for l in links:
            logger.debug("Link=%s" % (l,))

            if len(l.get("interface_ref")) != 2:
                logger.warning("Unable to manage extra-list of info (%d)!" %
                               len(l.get("interface_ref")))
                continue

            # is it really necessary to put bidirectional links?
#            self.__add_link_info(topology, l.get("interface_ref")[0].get("component_id"),
#                                 l.get("interface_ref")[1].get("component_id"),
#                                 l.get("link_type"))

            # store the values for the virtual island-to-island link
            self.__se_links.append(
                {'id': l.get("component_id"),
                 'source': l.get("interface_ref")[0].get("component_id"),
                 'destination': l.get("interface_ref")[1].get("component_id")})

            # we need to add "special" links here: SE-to-SDN, SE-to-TN
            # and an "abstract" link
            self.__add_se_external_link_info(
                topology, [l.get("interface_ref")[0].get("component_id"),
                           l.get("interface_ref")[1].get("component_id")])

    def __add_island2island_tnlink(self, info, tag):
        tn_src = info.get("source")
        tn_dst = info.get("destination")
        if MonitoringUtils.check_existing_tag_in_topology(tag, "link", self.TN2TN_LINK_TYPE, [tn_src, tn_dst]):
            return
        tn_ = etree.SubElement(tag, "link", type=self.TN2TN_LINK_TYPE, id=info.get("id"))
        etree.SubElement(tn_, "interface_ref", client_id=tn_src)
        etree.SubElement(
            tn_, "interface_ref", client_id=tn_dst)

    def __find_hybrid_endpoint(self, value):
        logger.debug("Finding the remote endpoint of %s" % (value,))
        for hybrid_link in self.__hybrid_links:
            logger.debug("HYBRID-link=%s" % (hybrid_link,))
            if hybrid_link.get("source") == value:
                return hybrid_link.get("destination")
            elif hybrid_link.get("destination") == value:
                return hybrid_link.get("source")

        return None

    def __add_island2island_lanlink(self, src, dst, tag):
        if MonitoringUtils.check_existing_tag_in_topology(tag, "link", self.MS_LINK_TYPE, [src, dst]):
            return
        logger.info("Lan link between %s and %s" % (src, dst,))
        if (src is not None) and (dst is not None):
            lan_ = etree.SubElement(tag, "link", type=self.MS_LINK_TYPE)
            etree.SubElement(lan_, "interface_ref", client_id=src)
            etree.SubElement(lan_, "interface_ref", client_id=dst)
        else:
            logger.error("Un-terminated lan link!")

    def __find_se_endpoint(self, value):
        logger.debug("Finding the remote endpoint of %s" % (value,))
        for se_link in self.__se_links:
            logger.debug("SE-link=%s" % (se_link,))
            if se_link.get("source") == value:
                return se_link.get("destination"), se_link.get("id")
            elif se_link.get("destination") == value:
                return se_link.get("source"), se_link.get("id")

        return None, None

    def __add_island2island_selink(self, ident, src, dst, tag):
        if MonitoringUtils.check_existing_tag_in_topology(tag, "link", self.MS_LINK_TYPE, [src, dst]):
            return
        logger.info("Se link (%s) between %s and %s" % (ident, src, dst,))
        if (ident is not None) and (src is not None) and (dst is not None):
            se_ = etree.SubElement(tag, "link", type=self.MS_LINK_TYPE, id=ident)
            etree.SubElement(se_, "interface_ref", client_id=src)
            etree.SubElement(se_, "interface_ref", client_id=dst)
        else:
            logger.error("Un-terminated or Unknown se link!")

    def __add_island2island_sdnif(self, src, dst, tag):
        logger.info("Sdn interfaces %s and %s" % (src, dst,))
        if (src is not None) and (dst is not None):
            etree.SubElement(tag, "interface_ref", client_id=src)
            etree.SubElement(tag, "interface_ref", client_id=dst)
        else:
            logger.error("Unknown sdn interfaces!")

    def add_island_to_island_links(self, slice_urn):
        if slice_urn not in self.__stored:
            logger.error("Unable to find Topology info from %s!" % slice_urn)
            return

        topology = self.__stored.get(slice_urn)
        logger.info("TN-links (%d), SE-links (%d), HYBRID-links (%d)" %
                    (len(self.__tn_links), len(self.__se_links),
                     len(self.__hybrid_links),))

        virtual_ = etree.SubElement(topology, "link", type="sdn")

        # Retrieve the SDN endpoints of the slice ("abstract link" in M/MS)
        se_link_urns = []
        for se_link in self.__hybrid_links:
            se_link_urns.extend([se_link.get("source"), se_link.get("destination")])
        se_link_urns = filter(lambda x: ":ofam" in x, se_link_urns)
        # TODO Check: what about >2 islands involved in the slice?
        # For loop (step: 2, reason: finding SDN#1 port <--> SDN#2 port)
        for i in xrange(0, len(se_link_urns), 2):
            self.__add_link_info(virtual_, se_link_urns[i], se_link_urns[i+1])

#        for sdn_link in self.__sdn_links:
#            logger.info("SDN-link=%s" % (sdn_link,))
#            # Adding inter-domain SDN-to-SDN links
#            self.__add_link_info(virtual_, sdn_link.get("source"), sdn_link.get("destination"), self.MS_LINK_TYPE)

        for se_link in self.__se_links:
#            if MonitoringUtils.check_existing_tag_in_topology(virtual_, "link", None, [se_link.get("source"), se_link.get("destination")]):
#                break
            logger.info("SE-link=%s" % (se_link,))
            # Adding SE-to-SDN or SE-to-TN link
            self.__add_link_info(virtual_, se_link.get("source"), se_link.get("destination"), self.MS_LINK_TYPE)

        for se_link in self.__hybrid_links:
#            if MonitoringUtils.check_existing_tag_in_topology(virtual_, "link", self.MS_LINK_TYPE, [se_link.get("source"), se_link.get("destination")]):
#                break
            logger.info("SE-hybrid-link=%s" % (se_link,))
            # Adding SE-to-SDN or SE-to-TN link
            self.__add_link_info(virtual_, se_link.get("source"), se_link.get("destination"), self.MS_LINK_TYPE)

        for tn_link in self.__tn_links:
            logger.info("TN-link=%s" % (tn_link,))

            # Add the tn link info into the virtual island2island info
            self.__add_island2island_tnlink(tn_link, virtual_)

            # Add the hybrid link between the source tn and se interface
            se_if_src = self.__find_hybrid_endpoint(tn_link.get("source"))
            self.__add_island2island_lanlink(
                tn_link.get("source"), se_if_src, virtual_)

            # Add the hybrid link between the destination tn and se interface
            se_if_dst = self.__find_hybrid_endpoint(tn_link.get("destination"))
            self.__add_island2island_lanlink(
                tn_link.get("destination"), se_if_dst, virtual_)

            # Add the se link in the "source" island
            se_internal_src, se_id_src = self.__find_se_endpoint(se_if_src)
            self.__add_island2island_selink(
                se_id_src, se_if_src, se_internal_src, virtual_)

            # Add the se link in the "destination" island
            se_internal_dst, se_id_dst = self.__find_se_endpoint(se_if_dst)
            self.__add_island2island_selink(
                se_id_dst, se_if_dst, se_internal_dst, virtual_)

            # Add the hybrid link between "source" se and sdn interface
            sdn_if_src = self.__find_hybrid_endpoint(se_internal_src)
            self.__add_island2island_lanlink(
                se_internal_src, sdn_if_src, virtual_)

            # Add the hybrid link between "destination" se and sdn interface
            sdn_if_dst = self.__find_hybrid_endpoint(se_internal_dst)
            self.__add_island2island_lanlink(
                se_internal_dst, sdn_if_dst, virtual_)

            # Finally, add the sdn interfaces
            self.__add_island2island_sdnif(sdn_if_src, sdn_if_dst, virtual_)


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
        topo = etree.SubElement(self.topology_list, "topology")
        # Milliseconds in UTC format
        topo.set("last_update_time", self.domain_last_update)
        topo.set("type", "slice")
        # TODO Retrieve from config OR from slice!
        # TODO Filter topology based on this!
        topo.set("name", "urn_of_slice")
        # TODO Retrieve owner from credentials
        topo.set("owner", "owner_of_slice")
        # Set topology tag as root node for subsequent operations
        self.topology = topo
