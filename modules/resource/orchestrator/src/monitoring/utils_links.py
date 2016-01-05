import copy
import core

logger = core.log.getLogger("monitoring-utils-links")


class MonitoringUtilsLinks(object):
    def __init__(self):
        pass

    ################
    # Set up link ID
    ################

    @staticmethod
    def get_id_for_link_crm_sdnrm(link_struct):
        link_id = ""
        # - Prepare link ID with the interfaces info
        if link_struct.get("dest_id").find("datapath") > -1:
            link_id = link_struct.get("dest_id")
            link_id_pre = link_struct.get("source_id")
        else:
            link_id = link_struct.get("source_id")
            link_id_pre = link_struct.get("dest_id")
        link_id = link_id[link_id.find("datapath+") + len("datapath") + 1:]
        link_id = "%s_%s" % (link_id_pre, link_id)
        # -- Adjust the URN (ID) to the expected format
        link_id = link_id.replace("+interface+", "+link+")
        return link_id

    @staticmethod
    def get_id_for_link_sdnrm_sdnrm(link_zip_list):
        link_id = ""
        # - Prepare link ID with the interfaces info
        dpid = link_zip_list[0][0]["component_id"]
        port = link_zip_list[0][1]["port_num"]
        link_id_pre = "%s_%s" % (dpid, port)
        dpid = link_zip_list[1][0]["component_id"]
        port = link_zip_list[1][1]["port_num"]
        link_id = "%s_%s" % (dpid, port)
        link_id = link_id[link_id.find("datapath+") + len("datapath") + 1:]
        link_id = "%s_%s" % (link_id_pre, link_id)
        # -- Adjust the URN (ID) to the expected format
        link_id = link_id.replace("+openflow:ocf", "+fms")
        link_id = link_id.replace(":ofam+datapath+", "+link+")
        return link_id

    @staticmethod
    def get_id_for_link_serm_sdnrm_tnrm(links):
        link = ""
        link_id = ""
        # - Prepare link ID with the interfaces info
        for link_struct in links:
            link = link_struct.get("component_id")
            if not link_id:
                link_id = link_struct.get("component_id")
                if link_id.find(":ofam+datapath+") > -1:
                    link_id = link_id.replace(":ofam+datapath+", "+link+")
                elif link_id.find(":serm+datapath+") > -1:
                    # Replace link in all but SE-TN links (where TN = "ogf")
                    if not any([ "ogf" in x for x in links ]):
                        link_id = link_id.replace(":serm+datapath+", "+link+")
            # - Contents from TN URNs are not replaced
            else:
                # - URN of TNRM STP is reduced to the NSI URN
                if link.find(":tnrm+stp+") > -1:
                    link = link[link.find(":tnrm+stp+") + len(":tnrm+stp+"):]
            if link.find("datapath+") > -1:
                link = link[link.find("datapath+") + len("datapath+"):]
        # - Adjust the URN (ID) to the expected format
        link_id = "%s_%s" % (link_id, link)
        return link_id

    @staticmethod
    def _translate_link_types(topology_tree):
#        topology_tree = etree.fromstring(self.get_topology())
#        filtered_links = topology_tree.xpath("//link")
        filtered_links = topology_tree.findall(".//link")
        for filtered_link in filtered_links:
            if filtered_link.get("link_type"):
                filtered_link.set("link_type", MonitoringUtilsLinks._translate_link_type(filtered_link))
            elif filtered_link.get("type"):
                filtered_link.set("type", MonitoringUtilsLinks._translate_link_type(filtered_link))
#        self.set_topology_tree(topology_tree)

    @staticmethod
    def _translate_link_type(link):
        # TODO - IMPORTANT FOR MS TO PARSE PROPERLY:
        #   Add others as needed in the future!
        default_type = "lan"
        
        ms_link_type_lan = "lan"
#        ms_link_type_static_link = "static_link"
#        ms_link_type_vlan_trans = "vlan_translation"
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

    @staticmethod
    def _set_dpid_port_from_link(component_id, link):
        mod_link = copy.deepcopy(link)
        # Keep component_id for further processing and then
        # retrieve the 2nd part of the link URN (with the resources)
        # E.g. "eth1-00:10:00:00:00:00:00:01_1"
        # And extract the DPID's port from there
        urn_split = component_id.split("+link+")[1]
        if "datapath" in mod_link.get("source_id"):
            dpid_port = urn_split.split("-")[0].split("_")[1]
            new_id = "%s_%s" % (mod_link.get("source_id"), dpid_port)
            mod_link["source_id"] = new_id
        elif "datapath" in mod_link.get("dest_id"):
            dpid_port = urn_split.split("-")[1].split("_")[1]
            new_id = "%s_%s" % (mod_link.get("dest_id"), dpid_port)
            mod_link["dest_id"] = new_id
        return mod_link
