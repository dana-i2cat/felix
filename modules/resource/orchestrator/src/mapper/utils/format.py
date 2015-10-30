class PathFinderTNtoSDNFormatUtils(object):

    @staticmethod
    def clean_tn_stp_cid(tn_stp_cid):
        # "Cleaning" means removing the TNRM prefix, ending in "tnrm+stp+"
        # This is performed for easier look up
        processed_tn_stp_cid = tn_stp_cid
        tnrm_prefix_location = processed_tn_stp_cid.rfind("tnrm+stp+")
        # Verify that there is such a substring before processing the URN
        if tnrm_prefix_location > 0:
            tnrm_prefix_location += len("tnrm+stp+")
            processed_tn_stp_cid = processed_tn_stp_cid[tnrm_prefix_location:]
        return processed_tn_stp_cid

    @staticmethod
    def format_verify_se_sdn_links(se_sdn_link):
        # Properly format the SE-SDN link to return a dictionary
        # with the values corresponding to each end of the link
        se_sdn_link_formatted = se_sdn_link
        # Iterate to find the location of the link containing 'ofam' on its CID
        sdn_link_location = [ "ofam" in c for c in se_sdn_link ].index(True)
        # The other position of the link is necessarily the SE link
        se_link_location = len(se_sdn_link) - 1 - sdn_link_location
        se_sdn_link_formatted = { "se": se_sdn_link[se_link_location], "sdn": se_sdn_link[sdn_link_location] }
        return se_sdn_link_formatted

    @staticmethod
    def format_verify_tn_interface(tn_interfaces_cids, tn_interface):
        # Ensure that the TN interfaces match with their original names
        # under resource.tn.node. This is performed to restore the
        # component_id values, previously changed
        tn_interface_formatted = tn_interface
        # Do not remove the TNRM prefix for this run
        for tn_interface_cid in tn_interfaces_cids:
            if tn_interface in tn_interface_cid:
                tn_interface_formatted = tn_interface_cid
                break
        return tn_interface_formatted

    @staticmethod
    def get_tn_interfaces_cid_from_node(tn_node, clean=False):
        # Return a tuple with a set of two component_id values for the given TN node
        interfaces = tn_node.get("interfaces", {})
        processed_interfaces = set()
        for interface in interfaces:
            processed_interface = interface.get("component_id", "")
            if clean == True:
                processed_interface = PathFinderTNtoSDNFormatUtils.clean_tn_stp_cid(processed_interface)
            processed_interfaces.add(processed_interface)
        # Convert from set to tuple to avoid unhashable problems later on
        return tuple(processed_interfaces)

    @staticmethod
    def remove_port_cid(cid):
        # Remove the port from the component_id
        # This is useful, for example, to search possible SDN links
        # connected to an SE node, by using an SE interface
        # whose port was previously removed
        processed_cid = cid
        port_section_location = processed_cid.rfind("_")
        processed_cid = processed_cid[:port_section_location]
        return processed_cid

