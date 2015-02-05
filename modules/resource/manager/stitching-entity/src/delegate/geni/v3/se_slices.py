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
        
    def set_link_db(self, slice_urn, end_time,links, nodes):
        print "end time in slice", end_time
        self._links_db[slice_urn] = self._create_sliver_from_req_n_and_l(end_time, links, nodes)

        #print nodes
        #print links
        #print slice_urn
        #self.__nodes[slice_urn] = nodes
        #self.__links[slice_urn] = links
        db_sync_manager.set_slices(slice_urn,{"nodes":nodes,"links":links,"slivers":self._links_db[slice_urn]})
    
    def remove_link_db(self, slice_urn):
        #del self._links_db[slice_urn]
        #del self.__nodes[slice_urn]
        #del self.__links[slice_urn]
        db_sync_manager.remove_slices(slice_urn)

    def get_link_db(self, slice_urn=None):
        
        if slice_urn:
            try:
                
                #links_db1 = self._links_db[slice_urn]
                #nodes1 = self.__nodes[slice_urn]
                #links1 = self.__links[slice_urn]
                slice_resources=db_sync_manager.get_slices(slice_urn)
                
                links_db = slice_resources["slivers"]
                nodes = slice_resources["nodes"]
                links = slice_resources["links"]
                
                return links_db, nodes, links
            except :
                return {}
                
    
    def _create_sliver_from_req_n_and_l( self, end_time, links, nodes):
        s_temp={}
        print "end time in slice2", end_time
        for l in links:
            
            temp =[]
           
            for interface in l['interface_ref']:
                
                for n in nodes:
                    for e in n['interfaces']:
                    
                        if interface.get('component_id') == e['component_id']:
                            
                            temp.append(e['vlan'])
          
            if s_temp.get("geni_sliver_urn") == None:
                s_temp["geni_sliver_urn"] = [{l["component_id"]:temp}]
                
            else:
                temp2 = s_temp.get("geni_sliver_urn")
                s_temp["geni_sliver_urn"] = list(temp2) + [{l["component_id"]:temp}]
                
        s_temp["geni_expires"] = end_time
        s_temp["geni_allocation_status"] = base.GENIv3DelegateBase.ALLOCATION_STATE_ALLOCATED   #ALLOCATION_STATE_UNALLOCATED
            
        return s_temp
    
    def _create_manifest_from_req_n_and_l(self, se_manifest,nodes,links):
        for n in nodes:
            se_manifest.node(n)
        
        for l in links:
            se_manifest.link(l)
            
    def _allocate_ports_in_slice(self, nodes):
        ports_take_part_info={'ports':[]}
        for n in nodes:
            for e in n['interfaces']:
                for vlan in e['vlan']:
                    current_vlan = vlan['tag']
                    current_port = e['component_id']
                    ports_take_part_info['ports'].append({'port' : current_port, 'vlan' : current_vlan})
        return ports_take_part_info
        