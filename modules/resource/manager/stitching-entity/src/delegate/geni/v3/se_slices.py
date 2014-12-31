
import base

class seSlicesWithSlivers(object):
    "Sliver element for se"
    def __init__(self):
        
        self.__nodes = []
        self.__links = []
        self.__slivers = {}
        self.__end_time = ''
        self.__se_manifest =''
        self._links_db = {}
        
    def set_link_db(self, slice_urn, end_time,links, nodes):
        print "end time in slice", end_time
        end3 = repr(end_time)
        self._links_db[slice_urn] = self._create_sliver_from_req_n_and_l(end_time, links, nodes)
        
    def get_link_db(self, slice_urn=None):
        
        if slice_urn:
            try:
                
                return self._links_db[slice_urn] 
            
            except :
                return {}
        return self._links_db 
    
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
        ports_take_part_info={}
        for n in nodes:
            for e in n['interfaces']:
                #print 'iface ', e['component_id']
                for vlan in e['vlan']:
                #print 'iface ',e['component_id']
                #print '    vlan tag ',vlan['tag']
                    if ports_take_part_info.get('ports') == None:
                        ports_take_part_info['ports'] = e['vlan']
                    else:
                        temp = ports_take_part_info['ports']
                        ports_take_part_info['ports'] = temp + e['vlan']
        
        #print str(e['vlan'])
        return ports_take_part_info
        