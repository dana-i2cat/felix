import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from db.db_manager import db_sync_manager
from mapper.utils.filter import PathFinderTNtoSDNFilterUtils as FilterUtils
from mapper.utils.format import PathFinderTNtoSDNFormatUtils as FormatUtils
from mapper.utils.combination import PathFinderTNtoSDNCombinationUtils as CombinationUtils

from pprint import pprint

#import itertools

class PathFinderTNtoSDN(object):

    def __init__(self, source_tn, destination_tn, *args, **kwargs):
        # CIDs of source and destination TN endpoints
        self.src_dom = source_tn
        self.dst_dom = destination_tn
        # Link type can be "nsi" or "gre". Empty means "all"
        self.link_type = kwargs.get("link_type", "")
        # Filters to match against required switches
        self.src_of_cids = kwargs.get("src_of_switch_cids", [])
        self.dst_of_cids = kwargs.get("dst_of_switch_cids", [])
        # Dummy list to reduce lines of code
        self.src_dst_values = [ "src", "dst" ]
        # Nodes and links from database
        self.tn_nodes = [ x for x in db_sync_manager.get_tn_nodes() ]
        self.se_links = [ x for x in db_sync_manager.get_se_links() ]
        # Mapping structure to be returned is a list of possible src-dst paths
        self.mapping_tn_se_of = []
        self.organisation_name_mappings = {
            "psnc": ["pionier"],
            "iminds": ["iMinds"],
            "kddi": ["jgn-x.jp"],  
        }
        # Update with parameters passed
        self.__dict__.update(kwargs)

    def get_organisation_mappings(self, organisation_name):
        # Return possible alternatives, given an organisation name
        return self.organisation_name_mappings.get(organisation_name, [organisation_name])

    def format_verify_tn_interface(self, tn_interface):
        # Ensure that the TN interfaces match with their original names
        # under resource.tn.node. This is performed to restore the
        # component_id values, previously changed
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=False)
        return FormatUtils.format_verify_tn_interface(tn_interfaces_cids, tn_interface)

    def get_tn_interfaces_cids(self, clean=False):
        # Return a list with the component_id values for the TN interfaces
        tn_interfaces = set()
        for tn_node in self.tn_nodes:
            tn_interfaces.update(FormatUtils.get_tn_interfaces_cid_from_node(tn_node, clean))
        return tn_interfaces

    def get_se_interfaces_cids(self, clean=False):
        # Return a list with the component_id values for the SE interfaces
        se_interfaces = set()
        for se_link in self.se_links:
            se_interfaces.add(FilterUtils.get_se_interfaces_cid_from_link(se_link, clean))
        return se_interfaces

    def find_tn_interfaces_for_domain(self, domain_name):
        # Given a domain name (e.g. "kddi", "aist"), find possible TN interfaces
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=True)
        domain_names_alt = self.get_organisation_mappings(domain_name)
        return FilterUtils.find_tn_interfaces_for_domain(tn_interfaces_cids, domain_names_alt, domain_name)

    def filter_tn_interfaces_by_type(self, tn_interfaces_cids, link_type=""):
        return FilterUtils.filter_tn_interfaces_by_type(tn_interfaces_cids, link_type)

    def find_se_interfaces_for_tn_interface(self, tn_interface):
        return FilterUtils.find_se_interfaces_for_tn_interface(self.se_links, tn_interface)

    def find_se_interfaces_for_domain_names(self, src_domain, dst_domain):
        mappings = self.organisation_name_mappings
        return FilterUtils.find_se_interfaces_for_domain_names(self.se_links, mappings, src_domain, dst_domain)

    def find_sdn_interfaces_for_se_interface(self, se_interface, negative_filter=[], possitive_filter=[""]):
        return FilterUtils.find_sdn_interfaces_for_se_interface(self.se_links, se_interface, negative_filter, possitive_filter)

    def find_se_sdn_links_for_se_node(self, se_node, negative_filter=[], possitive_filter=[""]):
        return FilterUtils.find_se_sdn_links_for_se_node(self.se_links, se_node, negative_filter, possitive_filter)

    def find_path_tn(self):
        # Retrieve list of CIDs for TNRM interfaces
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=True)

        # Get proper TN interfaces for both SRC and DST TN interfaces
        self.mapping_tn_se_of_src_partial = {}
        self.mapping_tn_se_of_dst_partial = {}

        # Get proper TN interfaces for (SRC, DST) TN interface
        for src_dst_value in self.src_dst_values:
            # Do a first clean of SRC and DST interface
            src_dst_cid = FormatUtils.clean_tn_stp_cid(getattr(self, "%s_dom" % src_dst_value))
            dst_src_tn_interface_found = False
            # Playing a bit with the language to be able
            # to have all the processing in a single place
            for tn_interface_cid in tn_interfaces_cids:
                if src_dst_cid in tn_interface_cid and src_dst_cid.startswith("urn"):
                    dst_src_tn_interface_found = True
                    break

            if dst_src_tn_interface_found == True:
                setattr(self, "tn_candidates_%s" % src_dst_value, [ src_dst_cid ])
            else:
                # Set is converted to list for easyness
                list_interfaces = map(list, self.find_tn_interfaces_for_domain(src_dst_cid))[0]
                # NOTE: only the first TN interface is retrieved...
                # Filter by link type, if requested by user
                setattr(self, "tn_candidates_%s" % src_dst_value, list(\
                    self.filter_tn_interfaces_by_type(list_interfaces, self.link_type)))

            # Initialize structure with dictionary and append SRC and DST interfaces to the set
            setattr(self, "mapping_tn_se_of_%s_partial" % src_dst_value, { "tn": set() })
            for tn_candidate in getattr(self, "tn_candidates_%s" % src_dst_value):
                mapping_partial = getattr(self, "mapping_tn_se_of_%s_partial" % src_dst_value)
                mapping_partial["tn"].add(tn_candidate)

        # Place every path into the final structure
        #combinations_src_dst_stps = zip(self.mapping_tn_se_of_src_partial["tn"], self.mapping_tn_se_of_dst_partial["tn"])
        # Find all possible combinations (order-independent)
        src_stps = self.mapping_tn_se_of_src_partial["tn"]
        dst_stps = self.mapping_tn_se_of_dst_partial["tn"]
        combinations_src_dst_stps = CombinationUtils.yield_combinations_stp_pairs(src_stps, dst_stps)
        # Filter out combinations whose STP have different types (i.e. NSI-GRE)
        combinations_src_dst_stps_filter = []
        for src_dst_stp in combinations_src_dst_stps:
            stp_link_tmp = FilterUtils.ensure_same_type_tn_interfaces([src_dst_stp[0], src_dst_stp[1]])
            if len(stp_link_tmp) == 2:
                combinations_src_dst_stps_filter.append(stp_link_tmp)
        combinations_src_dst_stps = combinations_src_dst_stps_filter
        for tn_src_dst_pair in combinations_src_dst_stps:
            # Tuple: 1st element (src), 2nd element (dst)
            self.mapping_tn_se_of.append({"src": {"tn": tn_src_dst_pair[0]}, "dst": {"tn": tn_src_dst_pair[1]}})

    def find_path_se(self):
        # Get SE interfaces for both SRC and DST TN interfaces
        for path_source in self.mapping_tn_se_of:
            for src_dst_value in self.src_dst_values:
                # Preparing list of links for SE-SDN
                path_source[src_dst_value]["links"] = []
                se_candidates = self.find_se_interfaces_for_tn_interface(path_source[src_dst_value]["tn"])
                # Fill mapping structure
                path_source[src_dst_value]["se"] = ""
                if len(se_candidates) > 0:
                    path_source[src_dst_value]["se"] = se_candidates[0]
        # Get SE interfaces without previous TN info
        # (case of static links between islands)
        # Assumption: name of 2 different islands/domains is provided
        if len(self.mapping_tn_se_of) == 0:
            partial_mapping = self.find_se_interfaces_for_domain_names(self.src_dom, self.dst_dom)
            mapping_tn_se_of_path = {}
            for src_dst_value in self.src_dst_values:
                src_dst_value_struct = {}
                for part in partial_mapping:
                    src_dst_domain = getattr(self, "%s_dom" % src_dst_value)
                    index_serm = [ src_dst_domain in l and "serm" in l for l in list(part) ].index(True)
                    index_sdnrm = len(part) - index_serm - 1
                    src_dst_value_struct = {}
                    src_dst_value_struct["se"] = part[index_serm]
                    part_mapping_sdn = part[index_sdnrm] if "ofam" in part[index_sdnrm] else None
                    # Only add proper links structure when both endpoints (SDN, SE) are correct
                    src_dst_value_struct["links"] = []
                    if part_mapping_sdn is not None:
                        src_dst_value_struct["links"] = [{"se": part[index_serm], "sdn": part_mapping_sdn }]
                # Add SE-SE paths for SRC and DST
                mapping_tn_se_of_path[src_dst_value] = src_dst_value_struct
            # Append to final structure
            self.mapping_tn_se_of.append(mapping_tn_se_of_path)
 
    def find_path_sdn(self):
        # Get SDN interfaces for (SRC, DST) SE interface
        negative_filter = [ "tnrm" ]
        for path_source in self.mapping_tn_se_of:
            for src_dst_value in self.src_dst_values:
                # Domains connected through the VPN may not have SE links (skip)
                if "se" not in path_source[src_dst_value]:
                    return
                #possitive_filter_of_switches = [ FormatUtils.remove_port_cid(f) for f in getattr(self, "%s_of_cids" % src_dst_value) ]
                se_interface = path_source[src_dst_value]["se"]
    
                # Possible SE-SDN links
                sdn_candidates = []
    
                if se_interface is not None and len(se_interface) > 0:
                    # Search for *every* connection between SE and SDN devices
                    se_node = FormatUtils.remove_port_cid(se_interface)
                    sdn_candidates = self.find_se_sdn_links_for_se_node(se_node, negative_filter)
        
                for se_sdn_link in sdn_candidates:
                    se_sdn_link = FormatUtils.format_verify_se_sdn_links(se_sdn_link)
                    path_source[src_dst_value]["links"].append(se_sdn_link)
    
    def format_structure(self):
        # Restore the full CID of the source and destination TN interfaces
        for mapping in self.mapping_tn_se_of:
            for src_dst_value in self.src_dst_values:
                # Domains connected through static links may not have "tn" data
                if "tn" in mapping[src_dst_value]:
                   mapping[src_dst_value]["tn"] = self.format_verify_tn_interface(mapping[src_dst_value]["tn"])
        # Remove paths where either source or destination are invalid
        self.mapping_tn_se_of = FilterUtils.prune_invalid_paths(self.mapping_tn_se_of)
        return self.mapping_tn_se_of

    def find_paths(self):
        # Find path from given TN to SDN, passing through SE      
        self.find_path_tn()
        self.find_path_se()
        self.find_path_sdn()
        # Prepare structure (clean up, correct, etc)
        self.mapping_tn_se_of = self.format_structure()
        return self.mapping_tn_se_of

if __name__ == "__main__":
    error_help = "Error using mapper. Usage: %s <src> <dst> [nsi|gre]" % (__file__)
    # SRC and DST are required
    if len(sys.argv) >= 3:
        src_name = sys.argv[1]
        dst_name = sys.argv[2]
    else:
        sys.exit(error_help)
    # Link type is optional
    if len(sys.argv) >= 4:
        link_type = sys.argv[3]
    else:
        link_type = ""

#    link_type = "nsi"
#    src_name = "urn:publicid:IDN+fms:aist:tnrm+stp+urn:ogf:network:pionier.net.pl:2013:topology:felix-ge-1-0-3"
#    dst_name = "urn:publicid:IDN+fms:aist:tnrm+stp+urn:ogf:network:jgn-x.jp:2013:topology:bi-felix-kddi-stp1"
#    src_of_switch_cids = [ "urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:00:54:e0:32:cc:a4:c0_11", "urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:00:08:81:f4:88:f5:b0_9" ]
#    dst_of_switch_cids = [ "urn:publicid:IDN+openflow:ocf:kddi:ofam+datapath+00:00:00:25:5c:e6:4f:07_2", "urn:publicid:IDN+openflow:ocf:kddi:ofam+datapath+00:00:00:25:5c:e6:4f:07_3" ]    

    optional = {
#        "src_of_switch_cids": src_of_switch_cids,
#        "dst_of_switch_cids": dst_of_switch_cids,
        "link_type": link_type,
    }
    path_finder_tn_sdn = PathFinderTNtoSDN(src_name, dst_name, **optional)
    pprint(path_finder_tn_sdn.find_paths())
