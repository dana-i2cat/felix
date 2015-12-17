from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser
from rspecs.tnrm.request_formatter import TNRMv3RequestFormatter
from db.db_manager import db_sync_manager
from commons import CommonUtils
from delegate.geni.v3 import exceptions as delegate_ex
from handler.geni.v3 import exceptions as geni_ex
from lxml import etree
from mapper.path_finder_tn_to_sdn import PathFinderTNtoSDN
from rspecs.commons import DEFAULT_XMLNS
from rspecs.commons_tn import generate_unique_link_id
from rspecs.tnrm.request_formatter import TNRMv3RequestFormatter

from core.config import ConfParser
import ast
import core
logger = core.log.getLogger("tn-utils")
import re

class TNUtils(CommonUtils):
    def __init__(self):
        super(TNUtils, self).__init__()
        w_ = ConfParser("ro.conf").get("tnrm")
        self.__workaround_split_allocation =\
            ast.literal_eval(w_.get("split_workaround"))

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = TNRMv3ManifestParser(from_string=m)
            logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            return ({"nodes": nodes, "links": links}, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e

    def manage_provision(self, peer, urns, creds, beffort, etime, gusers):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn = adaptor.provision(
                urns, creds[0]["geni_value"], beffort, etime, gusers)

            manifest = TNRMv3ManifestParser(from_string=m)
            logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            nodes = manifest.nodes()
            logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
            links = manifest.links()
            logger.info("Links(%d)=%s" % (len(links), links,))

            return ({"nodes": nodes, "links": links}, urn)
        except Exception as e:
            # It is possible that TNRM does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return ({"nodes": [], "links": []}, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def __update_node_route(self, route, values):
        ret = []
        for v in values:
            # This is a special case of the TNRM module and our deployment in
            # the FELIX testbed in which we have only 1 instance of TNRM and
            # all the islands refer to it. So, the MRO can have the same
            # resources but with different keys (out peers).
            keys = db_sync_manager.get_tn_node_routing_key(
                v.get("component_id"))
            logger.info("Node keys=%s" % (keys,))
            for k in keys:
                tmp = dict(v)
                tmp["routing_key"] = k
                ret.append(tmp)
                if k not in route:
                    route[k] = TNRMv3RequestFormatter()
        return ret

    def __update_link_route(self, route, values):
        ret = []
        for v in values:
            # please refer to the previous comment!
            keys = db_sync_manager.get_tn_link_routing_key(
                v.get("component_id"), v.get("component_manager_name"),
                [i.get("component_id") for i in v.get("interface_ref")])
            logger.info("Link keys=%s" % (keys,))
            for k in keys:
                tmp = dict(v)
                tmp["routing_key"] = k
                ret.append(tmp)
                if k not in route:
                    route[k] = TNRMv3RequestFormatter()
        return ret

    def __update_route_rspec(self, route, nodes, links):
        for key, rspec in route.iteritems():
            for n in nodes:
                if n.get("routing_key") == key:
                    rspec.node(n)
            for l in links:
                if l.get("routing_key") == key:
                    rspec.link(l)

    def __extract_se_from_tn(self, nodes, links):
        ret, ifref = [], set()
        for l in links:
            for p in l.get("property"):
                ifref.add(p.get("source_id"))
                ifref.add(p.get("dest_id"))

        for n in nodes:
            for i in n.get("interfaces"):
                if i.get("component_id") in ifref:
                    for v in i.get("vlan"):
                        ret.append({"vlan": v.get("tag"),
                                    "interface": i.get("component_id")})

        return ret

    def __manage_allocate_split_workaround(self, surn, creds, end, ns, ls):
        manifests, slivers, db_slivers, se_tn_info = [], [], [], []
        route = [(n.get("routing_key"), TNRMv3RequestFormatter()) for n in ns]
        for i in xrange(0, len(ns)):
            route[i][1].node(ns[i])
            route[i][1].link(ls[i])

        logger.info("(SPLIT_WORKAROUND)Route: %s" % (route,))
        for r in route:
            try:
                (m, ss) = self.send_request_allocate_rspec(
                    r[0], r[1], surn, creds, end)
                manifest = TNRMv3ManifestParser(from_string=m)
                logger.debug("(SPLIT_WORKAROUND)TNRMv3ManifestParser=%s" %
                             (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("(SPLIT_WORKAROUND)Nodes(%d)=%s" %
                            (len(nodes), nodes,))
                links = manifest.links()
                logger.info("(SPLIT_WORKAROUND)Links(%d)=%s" %
                            (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, r[0], slivers, db_slivers)

                se_tn = self.__extract_se_from_tn(nodes, links)
                logger.debug("(SPLIT_WORKAROUND)SE-TN-INFO=%s" % (se_tn,))
                if len(se_tn) > 0:
                    se_tn_info.extend(se_tn)
            except Exception as e:
                logger.critical("(SPLIT_WORKAROUND)exception: %s", e)
                raise e

        return (manifests, slivers, db_slivers, se_tn_info)

    def manage_allocate(self, surn, creds, end, nodes_in, links_in):
        route = {}
        nodes = self.__update_node_route(route, nodes_in)
        logger.debug("Nodes(%d)=%s" % (len(nodes), nodes,))
        links = self.__update_link_route(route, links_in)
        logger.debug("Links(%d)=%s" % (len(links), links,))

        if self.__workaround_split_allocation:
            # This is a (very)ugly workaround that we MUST remove ASAP!!!
            return self.__manage_allocate_split_workaround(surn, creds, end,
                                                           nodes, links)

        self.__update_route_rspec(route, nodes, links)
        logger.info("Route=%s" % (route,))

        manifests, slivers, db_slivers, se_tn_info = [], [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) =\
                    self.send_request_allocate_rspec(k, v, surn, creds, end)
                manifest = TNRMv3ManifestParser(from_string=m)
                logger.debug("TNRMv3ManifestParser=%s" % (manifest,))
                self.validate_rspec(manifest.get_rspec())

                nodes = manifest.nodes()
                logger.info("Nodes(%d)=%s" % (len(nodes), nodes,))
                links = manifest.links()
                logger.info("Links(%d)=%s" % (len(links), links,))

                manifests.append({"nodes": nodes, "links": links})

                self.extend_slivers(ss, k, slivers, db_slivers)

                se_tn = self.__extract_se_from_tn(nodes, links)
                logger.debug("SE-TN-INFO=%s" % (se_tn,))
                if len(se_tn) > 0:
                    se_tn_info.extend(se_tn)
            except Exception as e:
                logger.critical("manage_allocate exception: %s", e)
                raise delegate_ex.AllocationError(
                    str(e), surn, slivers, db_slivers)

        return (manifests, slivers, db_slivers, se_tn_info)

    @staticmethod
    def find_stps_from_links(links_in):
        ret = []
        # NOTE: "nsi" by default, but later on examined from CIDs URNs
        link_type = "nsi"
        for link in links_in:
            logger.debug("TNLink=%s" % (link,))
            if len(link.get("property")) > 0:
                # we use only the first item to identify the src/dst stps
                item = link.get("property")[0]
                if all(TNUtils.determine_stp_gre([item.get("source_id"), item.get("dest_id")])):
                    link_type = "gre"
                ret.append({"src_name": item.get("source_id"),
                            "dst_name": item.get("dest_id"),
                            "link_type": link_type})
        return ret

    @staticmethod
    def find_path_stps(src_stp, dst_stp, link_type):
        # If STPs involved in the request use consist of heterogeneous
        # types (e.g. NSI and GRE), warn user and raise exception
        stps_gre = TNUtils.determine_stp_gre([src_stp, dst_stp])
        if any(stps_gre) and not all(stps_gre):
            e = "Mapper SDN-SE-TN: attempting to connect 2 STPs"
            e += " of different type (e.g. GRE and NSI)"
            raise geni_ex.GENIv3GeneralError(e)
        path_finder_opt = {"link_type": link_type,}
        path_finder_tn_sdn = PathFinderTNtoSDN(src_stp, dst_stp, **path_finder_opt)
        paths = path_finder_tn_sdn.find_paths()
        logger.debug("Find PATH STPs=%s" % (paths,))
        return paths

    @staticmethod
    def find_interdomain_paths_from_tn_links(tn_links):
        paths = []
        stps = TNUtils.find_stps_from_links(tn_links)
        logger.debug("STPs=%s" % (stps,))

        for stp in stps:
            # If STPs involved in the request use
            # heterogeneous types for a given
            # connection (e.g. NSI and GRE), warn user and raise exception
            stps_gre = TNUtils.determine_stp_gre(
                [stp.get("src_name"), stp.get("dst_name")])
            if any(stps_gre) and not all(stps_gre):
                e = "Mapper SDN-SE-TN: attempting to connect 2 STPs"
                e += " of different type (e.g. GRE and NSI)"
                raise geni_ex.GENIv3GeneralError(e)
            path_finder_tn_sdn = PathFinderTNtoSDN(
                stp.get("src_name"), stp.get("dst_name"))
            paths = path_finder_tn_sdn.find_paths()
            # Mapper: raise an exception when a path *between
            # different authorities/islands* cannot be found
            #  src_auth = URNUtils.get_felix_authority_from_urn(
            #    stp.get("src_name"))
            #  dst_auth = URNUtils.get_felix_authority_from_urn(
            #    stp.get("dst_name"))
            #  if src_auth != dst_auth and len(paths) == 0:
            if len(paths) == 0:
                e = "Mapper SDN-SE-TN: cannot map inter-domain"
                e += " links for STPs provided. Possible causes:"
                e += " STPs cannot be connected or are located"
                e += " in the same island"
                raise geni_ex.GENIv3GeneralError(e)
        logger.debug("Found proper inter-domain paths=%s" % (paths,))
        return paths

    @staticmethod
    def find_used_tn_vlans():
        tn_vlans = dict()
        slice_monitoring = [ p for p in db_sync_manager.get_slice_monitoring_info() ]
        for slice_mon in slice_monitoring:
            if slice_mon is not None:        
                slice_mon_tree = etree.fromstring(slice_mon)
                #slice_mon_tree.xpath("link//link_type[contains(@name, '%s')]" % ("virtual_link"))
                #slice_mon_tree.xpath("link_type[@name='%s']" % ("tn"))
                #slice_mon_tree.xpath("topology_list//topology//link_type[@name='%s']" % ("tn"))
                tn_link = slice_mon_tree.xpath("topology//link[@type='tn'][contains(@id, 'urn')]")
                if tn_link is None:
                    break

                # Retrieve SRC and DST STP endpoints and their associated VLAN
                link_id = tn_link[0].get("id")                
                urn_reg = "urn.*(urn.*)\?vlan=(\d{1,4})-(urn.*)\?vlan=(\d{1,4})+.*"
                groups_reg = re.match(urn_reg, link_id)                
                urn_src, vlan_src, urn_dst, vlan_dst = [ groups_reg.group(i) for i in xrange(1,5) ]
                
                if urn_src not in tn_vlans:
                    tn_vlans[urn_src] = set([vlan_src])
                else:
                    tn_vlans[urn_src].add(vlan_src)
                if urn_dst not in tn_vlans:
                    tn_vlans[urn_dst] = set([vlan_dst])
                else:
                    tn_vlans[urn_dst].add(vlan_dst)
        return tn_vlans

    @staticmethod
    def check_vlan_is_in_use(vlan):
        """Determine whether a TN VLAN is already in use (True) or not (False)"""
        is_contained = False
        used_vlans = TNUtils.find_used_tn_vlans()
        used_vlans_list = map(lambda x: list(x), used_vlans.values())
        used_vlans_set = set(map(lambda x: x[0], used_vlans_list))
        if not isinstance(vlan, list):
            vlan = [vlan]
        contained_vlans = used_vlans_set.intersection(vlan)
        if len(contained_vlans) > 0:
            is_contained = True
        return (is_contained, contained_vlans)

    @staticmethod
    def determine_stp_gre(stp):
        """Determine whether all involved STPs are gre (True) or not (False)"""
        if not isinstance(stp, list):
            stp = [stp]
        return map(lambda x: ":gre:" in x, stp)

    @staticmethod
    def fill_name_tag_in_tn_iface(node, dom):
        new_node = {}
        num_iter = 0
        vlan = ""
        for k in node.keys():
            if k == "vlan":
                vlans = node[k][0]["description"].split("-")
                is_contained = True
                max_iter = int(vlans[1])-int(vlans[0])+1
                # Search for suitable (available VLANs) until found or "all" the 
                # range (having in mind the randomness) has been examined
                while is_contained or num_iter >= max_iter:
                    vlan = str(CommonUtils.get_random_range_value(vlans[0], vlans[1]))
                    is_contained, intersect = TNUtils.check_vlan_is_in_use(vlan)
                    num_iter+=1
                new_node[k] = [{"tag": vlan, "name": "%s+vlan" % dom}]
            else:
                new_node[k] = node[k]
        return new_node

    @staticmethod
    def generate_tn_node(src_dom, dst_dom):
        src_node = db_sync_manager.get_tn_node_interface({"component_id": src_dom})
        dst_node = db_sync_manager.get_tn_node_interface({"component_id": dst_dom})
        if len(src_node) == 0 or len(dst_node) == 0:
            logger.warning("Problem obtaining TN nodes: invalid endpoints (%s, %s)" % (src_dom, dst_dom))
            return None
        else:
            src_node = src_node[0]
            dst_node = dst_node[0]
        src_iface_new = TNUtils.fill_name_tag_in_tn_iface(src_node, src_dom)
        dst_iface_new = TNUtils.fill_name_tag_in_tn_iface(dst_node, dst_dom)

        # Assumption: just one TN node
        node = db_sync_manager.get_tn_nodes()[0]
        node["interfaces"] = [src_iface_new, dst_iface_new]
        return node

    @staticmethod
    def generate_tn_link(src_dom, src_vlan, dst_dom, dst_vlan):
        tn_ref_node = db_sync_manager.get_tn_nodes()[0]
        link_cid = tn_ref_node.get("component_id", "")
        link_clid = generate_unique_link_id(link_cid, src_dom, dst_dom)

        stp_reg = "stp+"
        src_dom_ogf = src_dom[src_dom.find(stp_reg)+len(stp_reg):]
        dst_dom_ogf = dst_dom[dst_dom.find(stp_reg)+len(stp_reg):]
        link_clid = "%s+%s?vlan=%s-%s?vlan=%s" % (link_cid, src_dom_ogf, src_vlan, dst_dom_ogf, dst_vlan)
        logger.debug("Chosen TN inter-domain link: %s" % link_clid)

        link = {"component_id": link_clid,
            "component_manager_name": tn_ref_node.get("component_manager_id", ""),
            "interface_ref": [{"component_id": src_dom}, {"component_id": dst_dom,}],
            "property": [{"capacity": "100", "source_id": src_dom, "dest_id": dst_dom},
                        {"capacity": "100", "source_id": dst_dom, "dest_id": src_dom}],
            "component_manager_uuid": None,
            "vlantag": None,
            }
        return link

    @staticmethod
    def identify_tn_from_sdn_and_vl(dpid_port_ids, request_stps, sdn_utils):
        # TN resources
        se_tn_info = None
        nodes = []
        links = []
        logger.debug("Identifying TN STPs from Virtual Links and SDN resources")
        logger.debug("Request STPs=%s" % str(request_stps))
        for stp in request_stps:
            paths = TNUtils.find_path_stps(stp.get("src_name"), stp.get("dst_name"), \
                stp.get("link_type"))
            # Mapper: raise an exception when a path *between
            # different authorities/islands* cannot be found
            if len(paths) == 0:
                e = "Mapper SDN-SE-TN: cannot map inter-domain links for STPs provided. Possible"
                e += " causes: STPs have invalid type or are located in the same island"
                raise geni_ex.GENIv3GeneralError(e)

            # A path is chosen from the mapping taking into account the
            # restrictions defined implicitly by the DPIDs within the flowspace
            # Note: an empty list will be returned if none fits
            path = sdn_utils.find_path_containing_all(dpid_port_ids, paths)
            # Thus, path is either the previously returned (or all, if empty)
            path = path or paths
            # Whatever the search space (i.e. the path) is, this is fed to the
            # methods that identify how to extend the SDN flowspace to be able
            # to bind the SDN domain with the stitching (virtual) domain
            items, links_constraints = sdn_utils.analyze_mapped_path(dpid_port_ids, path)

            # Getting the only element of list (path) or random element (paths)
            rnd_path_idx = CommonUtils.get_random_list_position(len(paths))
            path = path[0] if len(path) == 1 else paths[rnd_path_idx]
            src_dom, dst_dom = path["src"]["tn"], path["dst"]["tn"]

            node = TNUtils.generate_tn_node(src_dom, dst_dom)
            src_vlan = node["interfaces"][0]["vlan"][0]["tag"]
            dst_vlan = node["interfaces"][1]["vlan"][0]["tag"]
            if node is None:
                break
            nodes.append(node)
            link = TNUtils.generate_tn_link(src_dom, src_vlan, dst_dom, dst_vlan)
            links.append(link)
        return (nodes, links)

    @staticmethod
    def add_tn_to_ro_request_rspec(req_rspec, sdn_utils, vl_utils):
        """
        Should only be run from MRO; where TN can be processed.
        """
        # Run mapper path-finder to extend SDN resources
        # by adding an inherent link to the SE device
        # Note: check if we had an explicit/direct TN allocation
        # (in this case just skip the mapper)
        request_stps = []
        # Retrieve virtual links
        if CommonUtils.is_virtual_links(req_rspec):
            vlinks = req_rspec.vl_links()
            for vlink in vlinks:
                (src_dom, dst_dom) = vl_utils.get_domains_from_link(vlink)
                request_stps_type = vl_utils.get_type_from_link(vlink)
                request_stps.append({"src_name": src_dom, "dst_name": dst_dom, \
                    "link_type": request_stps_type})

        logger.debug("STPs=%s" % (request_stps,))
        dpid_port_ids = sdn_utils.find_dpid_port_identifiers(
            req_rspec.of_groups(), req_rspec.of_matches())
        logger.debug("DPIDs=%s" % (dpid_port_ids,))

        tn_nodes = []
        tn_links = []
        try:
            tn_nodes, tn_links = TNUtils.identify_tn_from_sdn_and_vl(dpid_port_ids, request_stps, sdn_utils)
        except Exception as e:
            m = "Could not obtain TN resources from SDN and VL resources. Details: %s" % str(e)
            logger.warning(m)

        tnrm_formatter = TNRMv3RequestFormatter()
        for n in tn_nodes:
            tnrm_formatter.node(n)
        for l in tn_links:
            tnrm_formatter.link(l)

        # Generate RSpec from request RSpec object
        rspec = req_rspec.get_rspec()
        tnrm_rspec = tnrm_formatter.rspec.getchildren()
        for tnrm_elem in tnrm_rspec:
            rspec.append(tnrm_elem)

        # Clean virtual links
        vlinks = rspec.xpath("xs:link//xs:link_type[contains(@name, '%s')]" % ("virtual_link"), namespaces={"xs": DEFAULT_XMLNS})
        #vlinks = rspec.xpath("xs:link//xs:link_type[@name='%s']" % ("urn:felix+virtual_link"), namespaces={"xs": DEFAULT_XMLNS})
        #vlinks = rspec.findall("{%s}link//{%s}link_type[@name='%s']" % (DEFAULT_XMLNS, DEFAULT_XMLNS, "urn:felix+virtual_link"))
        for v in vlinks:
            v.getparent().getparent().remove(v.getparent())
        rspec = etree.tostring(rspec, pretty_print=True)

        logger.debug("Implicit request => request RSpec has been extended with proper resources")
        logger.debug("Request RSpec passed to Allocate: %s" % str(rspec))
        return rspec
