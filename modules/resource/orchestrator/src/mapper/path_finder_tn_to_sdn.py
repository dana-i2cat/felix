from db.db_manager import db_sync_manager
from pprint import pprint

import itertools

class PathFinderTNtoSDN(object):

    def __init__(self, source_tn, destination_tn, *args, **kwargs):
        # CIDs of source and destination TN endpoints
        self.src_tn = source_tn
        self.dst_tn = destination_tn
        # Filters to match against required switches
        self.src_of_cids = []
        self.dst_of_cids = []
        # Dummy list to reduce lines of code
        self.src_dst_values = [ "src", "dst" ]
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

    def remove_port_cid(self, cid):
        # Remove the port from the component_id
        # This is useful, for example, to search possible SDN links
        # connected to an SE node, by using an SE interface
        # whose port was previously removed
        processed_cid = cid
        port_section_location = processed_cid.rfind("_")
        processed_cid = processed_cid[:port_section_location]
        return processed_cid

    def format_verify_se_sdn_links(self, se_sdn_link):
        # Properly format the SE-SDN link to return a dictionary
        # with the values corresponding to each end of the link
        se_sdn_link_formatted = se_sdn_link
        # Iterate to find the location of the link containing 'ofam' on its CID
        sdn_link_location = [ "ofam" in c for c in se_sdn_link ].index(True)
        # The other position of the link is necessarily the SE link
        se_link_location = len(se_sdn_link) - 1 - sdn_link_location
        se_sdn_link_formatted = { "se": se_sdn_link[se_link_location], "sdn": se_sdn_link[sdn_link_location] }
        return se_sdn_link_formatted

    def format_verify_tn_interface(self, tn_interface):
        # Ensure that the TN interfaces match with their original names
        # under resource.tn.node. This is performed to restore the
        # component_id values, previously changed
        tn_interface_formatted = tn_interface
        # Do not remove the TNRM prefix for this run
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=False)
        for tn_interface_cid in tn_interfaces_cids:
            if tn_interface in tn_interface_cid:
                tn_interface_formatted = tn_interface_cid
                break
        return tn_interface_formatted

    def get_tn_interfaces_cid_from_node(self, tn_node, clean=False):
        # Return a tuple with a set of two component_id values for the given TN node
        interfaces = tn_node.get("interfaces", {})
        processed_interfaces = set()
        for interface in interfaces:
            processed_interface = interface.get("component_id", "")
            if clean == True:
                processed_interface = self.clean_tn_stp_cid(processed_interface)
            processed_interfaces.add(processed_interface)
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(processed_interfaces)

    def get_tn_interfaces_cids(self, clean=False):
        # Return a list with the component_id values for the TN interfaces
        tn_interfaces = set()
        for tn_node in tn_nodes:
            tn_interfaces.update(self.get_tn_interfaces_cid_from_node(tn_node, clean))
        return tn_interfaces

    def clean_tn_stp_cid(self, tn_stp_cid):
        # "Cleaning" means removing the TNRM prefix, ending in "tnrm+stp+"
        # This is performed for easier look up
        processed_tn_stp_cid = tn_stp_cid
        tnrm_prefix_location = processed_tn_stp_cid.rfind("tnrm+stp+")
        # Verify that there is such a substring before processing the URN
        if tnrm_prefix_location > 0:
            tnrm_prefix_location += len("tnrm+stp+")
            processed_tn_stp_cid = processed_tn_stp_cid[tnrm_prefix_location:]
        return processed_tn_stp_cid

    def get_se_interfaces_cid_from_link(self, se_link, clean=False):
        # Return a list with a set of two component_id values for the given SE link
        interfaces = se_link.get("interface_ref", {})
        processed_interfaces = []
        for interface in interfaces:
            processed_interface = interface.get("component_id", "")
            if clean == True:
                # Some of the SE links are SE-TN links
                processed_interface = self.clean_tn_stp_cid(processed_interface)
            processed_interfaces.append(processed_interface)
        return list(set(processed_interfaces))

    def get_se_interfaces_cids(self, clean=False):
        # Return a list with the component_id values for the SE interfaces
        se_interfaces = set()
        for se_link in se_links:
            se_interfaces.add(get_se_interfaces_cid_from_link(se_link, clean))
        return se_interfaces

    def find_tn_interfaces_for_domain(self, domain_name):
        # Given a domain name (e.g. "kddi", "aist"), find possible TN interfaces
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=True)
        domain_names_alt = self.get_organisation_mappings(domain_name)    
        domain_name_alt_matches = set()    
        tn_interfaces_match = []
        # A set is used to add possible TN interfaces. This avoids duplications
        for domain_name_alt in domain_names_alt:
            domain_name_alt_matches.add(tuple(s for s in tn_interfaces_cids if domain_name_alt in s))
        return domain_name_alt_matches

    def find_se_interfaces_for_tn_interface(self, tn_interface):
        se_interfaces_match = set()
        for se_link in se_links:
            if tn_interface in se_link.get("component_id"):
                se_link_interfaces = [ self.clean_tn_stp_cid(iface.get("component_id")) for iface in se_link.get("interface_ref") ]
                # Remove link interface that matches with the passed TN interface
                se_link_interfaces.pop(se_link_interfaces.index(tn_interface))
                se_interfaces_match.add(se_link_interfaces[0])
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(se_interfaces_match)

    def find_sdn_interfaces_for_se_interface(self, se_interface, negative_filter=[], possitive_filter=[""]):
        sdn_interfaces_match = set()
        for se_link in se_links:
            se_link_interfaces = [ iface.get("component_id") for iface in se_link.get("interface_ref") ]
            se_link_interfaces_match = any([ self.remove_port_cid(se_interface) in se_link_interface for se_link_interface in se_link_interfaces ])
            if se_link_interfaces_match:
                # Retrieve link interfaces from SDN switches that are connected with any SE interface
                # Search for some SDN link connected to the passed SE component id (without port!)
                se_interface_noport = self.remove_port_cid(se_interface)
                # Also, avoid adding links SE-TN (this would introduce a never-ending loop)
                if se_interface_noport in se_link_interfaces[0] \
                        and not any([ param in se_link_interfaces[1] for param in negative_filter ]) \
                        and any([ param in se_link_interfaces[1] for param in possitive_filter ]):
                    sdn_interfaces_match.add(se_link_interfaces[1])
                elif se_interface_noport in se_link_interfaces[1] \
                        and not any([ param in se_link_interfaces[0] for param in negative_filter ]) \
                        and any([ param in se_link_interfaces[0] for param in possitive_filter ]):
                    sdn_interfaces_match.add(se_link_interfaces[0])
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(sdn_interfaces_match)

    def find_se_sdn_links_for_se_node(self, se_node, negative_filter=[], possitive_filter=[""]):
        sdn_se_links = set()
        for se_link in se_links:
            se_link_interfaces = [ iface.get("component_id") for iface in se_link.get("interface_ref") ]
            se_link_interfaces_match = any([ se_node in se_link_interface for se_link_interface in se_link_interfaces ])
            if se_link_interfaces_match:
                # Retrieve link interfaces from SDN switches that are connected with any SE interface
                # Search for some SDN link connected to the passed SE component id (without port!)
                se_interface_noport = se_node
                # Also, avoid adding links SE-TN (this would introduce a never-ending loop)
                if se_interface_noport in " ".join(se_link_interfaces[:]) and \
                        not any([ param in " ".join(se_link_interfaces[:]) for param in negative_filter ]) and \
                        any([ param in " ".join(se_link_interfaces[:]) for param in possitive_filter ]):
                    sdn_se_links.add(tuple(se_link_interfaces))
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(sdn_se_links)

    def prune_invalid_paths(self, mapping_path_structure):
        new_mapping_path_structure = []
        for idx, mapping_path_element in enumerate(mapping_path_structure):
            cond_idx = all( [ len(mapping_path_element["src"][elem]) > 0 for elem in mapping_path_element["src"] ]) \
                and all( [ len(mapping_path_element["dst"][elem]) > 0 for elem in mapping_path_element["dst"] ])
            if all( [ len(mapping_path_element["src"][elem]) > 0 for elem in mapping_path_element["src"] ]) \
                and all( [ len(mapping_path_element["dst"][elem]) > 0 for elem in mapping_path_element["dst"] ]):
                new_mapping_path_structure.append(mapping_path_element)
        return new_mapping_path_structure

    def find_path_tn(self):
        # Retrieve list of CIDs for TNRM interfaces
        tn_interfaces_cids = self.get_tn_interfaces_cids(clean=True)
        
        # Get proper TN interfaces for both SRC and DST TN interfaces
        tn_candidates = []
        self.mapping_tn_se_of_src_partial = {}
        self.mapping_tn_se_of_dst_partial = {}

        # Get proper TN interfaces for (SRC, DST) TN interface
        for src_dst_value in self.src_dst_values:
            # Do a first clean of SRC and DST interface
            src_dst_cid = self.clean_tn_stp_cid(getattr(self, "%s_tn" % src_dst_value))
            dst_src_tn_interface_found = False
            # Playing a bit with the language to be able
            # to have all the processing in a single place
            for tn_interface_cid in tn_interfaces_cids:
                if src_dst_cid in tn_interface_cid and src_dst_cid.startswith("urn"):
                    dst_src_tn_interface_found = True
            if  dst_src_tn_interface_found == True:
                setattr(self, "tn_candidates_%s" % src_dst_value, [ src_dst_cid ])
            else:
                # Set is converted to list for easyness
                # NOTE Only the first TN interface is retrieved...
                setattr(self, "tn_candidates_%s" % src_dst_value, list(self.find_tn_interfaces_for_domain(src_dst_cid))[0])

            # Initialize structure with dictionary and append SRC and DST interfaces to the set
            setattr(self, "mapping_tn_se_of_%s_partial" % src_dst_value, { "tn": set() })
            for tn_candidate in getattr(self, "tn_candidates_%s" % src_dst_value):
                mapping_partial = getattr(self, "mapping_tn_se_of_%s_partial" % src_dst_value)
                mapping_partial["tn"].add(tn_candidate)

        # Place every path into the final structure
        combinations_src_dst_stps = zip(self.mapping_tn_se_of_src_partial["tn"], self.mapping_tn_se_of_dst_partial["tn"])
        # Find all possible combinations (order-independent)
    #    combinations_src_dst_stps = [zip(x,self.mapping_tn_se_of_dst_partial["tn"]) for x in itertools.combinations(self.mapping_tn_se_of_src_partial["tn"], len(self.mapping_tn_se_of_dst_partial["tn"]))][0]
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
    
    def find_path_sdn(self):
        # Get SDN interfaces for (SRC, DST) SE interface
        negative_filter = [ "tnrm" ]
        for path_source in self.mapping_tn_se_of:
            for src_dst_value in self.src_dst_values:
                possitive_filter_of_switches = [ self.remove_port_cid(f) for f in getattr(self, "%s_of_cids" % src_dst_value) ]
                se_interface = path_source[src_dst_value]["se"]
    
                # Possible SE-SDN links
                sdn_candidates = []
    
                if se_interface is not None and len(se_interface) > 0:
                    # Search for *every* connection between SE and SDN devices
                    se_node = self.remove_port_cid(se_interface)
                    sdn_candidates = self.find_se_sdn_links_for_se_node(se_node, negative_filter)
        
                for se_sdn_link in sdn_candidates:
                    se_sdn_link = self.format_verify_se_sdn_links(se_sdn_link)
                    path_source[src_dst_value]["links"].append(se_sdn_link)
    
    def format_structure(self):
        # Restore the full CID of the source and destination TN interfaces
        for mapping in self.mapping_tn_se_of:
            for src_dst_value in self.src_dst_values:
                mapping[src_dst_value]["tn"] = self.format_verify_tn_interface(mapping[src_dst_value]["tn"])
        # Remove paths where either source or destination are invalid
        self.mapping_tn_se_of = self.prune_invalid_paths(self.mapping_tn_se_of)
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
	# Link PSNC-KDDI
#    src_name ="psnc"
#    dst_name = "kddi"

	# Link PSNC-KDDI
    src_name = "urn:publicid:IDN+fms:aist:tnrm+stp+urn:ogf:network:pionier.net.pl:2013:topology:felix-ge-1-0-3"
    dst_name = "urn:publicid:IDN+fms:kddi:tnrm+stp+urn:ogf:network:jgn-x.jp:2013:topology:bi-felix-kddi-stp1"

	# Link AIST-KDDI
#    src_name = "urn:publicid:IDN+fms:aist:tnrm+stp+urn:ogf:network:aist.go.jp:2013:topology:bi-se1"
#    dst_name = "urn:publicid:IDN+fms:kddi:tnrm+stp+urn:ogf:network:jgn-x.jp:2013:topology:bi-felix-kddi-stp1"

    # --------
   
    src_of_switch_cids = [ "urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:00:54:e0:32:cc:a4:c0_11", "urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:00:08:81:f4:88:f5:b0_9" ]
    dst_of_switch_cids = [ "urn:publicid:IDN+openflow:ocf:kddi:ofam+datapath+00:00:00:25:5c:e6:4f:07_2", "urn:publicid:IDN+openflow:ocf:kddi:ofam+datapath+00:00:00:25:5c:e6:4f:07_3" ]    

    optional = {
        "src_of_switch_cids": src_of_switch_cids,
        "dst_of_switch_cids": dst_of_switch_cids,
    }
    path_finder_tn_sdn = PathFinderTNtoSDN(src_name, dst_name, **optional)
    pprint(path_finder_tn_sdn.find_paths())

