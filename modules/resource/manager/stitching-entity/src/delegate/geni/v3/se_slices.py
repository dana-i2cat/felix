from delegate.geni.v3.db_manager_se import db_sync_manager
import base

class seSlicesWithSlivers(object):
    "Sliver element for se"
    def __init__(self):
        
        self.__nodes = {}
        self.__links = {}
        self.__slivers = {}
        self.__end_time = ''
        self.__se_manifest =''
        self._links_db = {}
        
    def set_link_db(self, slice_urn, end_time,links, nodes, sliceVlansPairs):
        self._links_db[slice_urn] = self._create_sliver_from_req_n_and_l(end_time, links, nodes)
        db_sync_manager.set_slices(slice_urn,{"nodes":nodes,"links":links,"slivers":self._links_db[slice_urn],"vlan-pairs":sliceVlansPairs})
    
    def remove_link_db(self, slice_urn):
        #del self._links_db[slice_urn]
        #del self.__nodes[slice_urn]
        #del self.__links[slice_urn]
        db_sync_manager.remove_slices(slice_urn)

    def get_slice_vlan_pairs(self, slice_urn):
        if slice_urn:
            try:

                slice_resources=db_sync_manager.get_slices(slice_urn)
                sliceVlansPairs = slice_resources["vlan-pairs"]
                
                return sliceVlansPairs
            except :
                return {}

    def get_link_db(self, slice_urn=None):
        
        if slice_urn:
            try:

                slice_resources=db_sync_manager.get_slices(slice_urn)
                links_db = slice_resources["slivers"]
                sliver_tmp = []
                for sliver in links_db["geni_sliver_urn"]:
                    sliver_tmp.append(sliver.keys()[0])
                links_db["geni_sliver_urn"] = sliver_tmp
                # links_db["geni_sliver_urn"] = links_db["geni_sliver_urn"][0].keys()[0]
                nodes = slice_resources["nodes"]
                links = slice_resources["links"]
                sliver_id = links[0]["sliver_id"]
                
                return links_db, nodes, links
            except :
                return {}
                
    
    def _create_sliver_from_req_n_and_l( self, end_time, links, nodes):
        s_temp={}
        for l in links:
            
            temp =[]
           
            for interface in l['interface_ref']:
                
                for n in nodes:
                    for e in n['interfaces']:
                    
                        if interface.get('component_id') == e['component_id']:
                            
                            temp.append(e['vlan'])
          
            if s_temp.get("geni_sliver_urn") == None:
                s_temp["geni_sliver_urn"] = [{l["sliver_id"]:temp}]
            else:
                temp2 = s_temp.get("geni_sliver_urn")
                s_temp["geni_sliver_urn"] = list(temp2) + [{l["sliver_id"]:temp}]
                
        s_temp["geni_expires"] = end_time
        # s_temp["__all_sliver_vlan_pairs__"] = sliceVlansPairs
        s_temp["geni_allocation_status"] = base.GENIv3DelegateBase.ALLOCATION_STATE_ALLOCATED   #ALLOCATION_STATE_UNALLOCATED
        s_temp["geni_operational_status"] = "geni_notready"
            
        return s_temp
    
    def _create_manifest_from_req_n_and_l(self, se_manifest,nodes,links,sliceVlansPairs):
        # TODO: Check if sliver_urn is valid for RO
        vlans = []
        vlanOnPort = []
        for n in nodes:
            for vlan in n["interfaces"]:
                for vlan_tag  in vlan["vlan"]:
                    vlans.append(vlan_tag["tag"])
                    vlanOnPort.append({vlan["component_id"]:vlan_tag["tag"]})
            se_manifest.node(n)

        for l in links:
            # Check if there is "felix:vlan" in link request
            if sliceVlansPairs != None:
                component_id = l["component_id"]
                for vlanPairs in sliceVlansPairs:
                    _client_id, _in_interface, _out_interface = vlanPairs
                    if _client_id == component_id:
                        _in_vlan = _in_interface["vlan"]
                        _in_port = _in_interface["port_id"].split("_")[-1]
                        _out_vlan = _out_interface["vlan"]
                        _out_port = _out_interface["port_id"].split("_")[-1]
                    l['__vlan_pairs__'] = [_in_port, _in_vlan, _out_port, _out_vlan] 

                l['vlantag'] = _in_vlan + "-" + _out_vlan
                sliver_id_name = l["component_id"] + "_" + _in_vlan + "_" + _out_vlan
                sliver_id_name = sliver_id_name.replace("datapath", "sliver")
                l['sliver_id'] = sliver_id_name

                se_manifest.link(l)
            else:
                raise Exception("Slice has been created. Error in creating Manifest. Missing 'felix:vlan' parameter or no VLAN parameter in RSpec request.")
            
    def _allocate_ports_in_slice(self, nodes):
        ports_take_part_info={'ports':[]}
        for n in nodes:
            for e in n['interfaces']:
                for vlan in e['vlan']:
                    current_vlan = vlan['tag']
                    current_port = e['component_id']
                    ports_take_part_info['ports'].append({'port' : current_port, 'vlan' : current_vlan})
        return ports_take_part_info
        
