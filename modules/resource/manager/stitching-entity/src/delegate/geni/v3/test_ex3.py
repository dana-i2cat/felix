from delegate_v3 import GENIv3Delegate
import se_configurator as SEConfigurator
from nose import with_setup
from datetime import datetime, timedelta

#Testing Configuration

test_conf ="""organisation: psnc
dpid: 00:00:00:00:00:00:00:01

provision_plugin: ryu_rest_of # possible values:
                                # * ryu_rest_of (default)
                                # * pox_xmlrpc_of

vlan_trans: true
qinq: false
capacity: 1G


interfaces:
    "1":
        remote_endpoints: 
            -
                name: urn:publicid:IDN+fms:psnc:tnrm+stp+urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_11
                type: vlan_trans
                vlans:
                    - 1000
                    - 1100
                    - 3100

    "2":
        remote_endpoints:
            -
                name: urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_6
                type: vlan_trans
                vlans:
                    - 2000
                    - 2100

    "3":
        remote_endpoints:
            -
                name: urn:publicid:IDN+fms:psnc:tnrm+stp+urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_12
                type: vlan_trans
                vlans:
                    - 3000

    "4":
        remote_endpoints:
            -
                name: urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_7
                type: vlan_trans
                vlans:
                    - 4000
                    - 4100"""
    

def get_nodes_dict_for_rspec_setup_function():
    
    global all_nodes
    all_nodes=  [{'exclusive': 'false', 'interfaces': [{'component_id': u'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1', 'vlan': []}, {'component_id': u'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3', 'vlan': []}, {'component_id': u'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2', 'vlan': []}, {'component_id': u'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4', 'vlan': []}], 'component_manager_id': 'urn:publicid:IDN+fms:psnc:serm+authority+cm', 'sliver_type_name': None, 'component_id': 'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01'}]
    
    return all_nodes
  

def get_nodes_dict_for_rspec_teardown_function1():
    
    pass   
 
 

def get_links_dict_for_rspec_setup_function():
    global all_links
    all_links = [{'property': [{'source_id': '*', 'dest_id': '*', 'capacity': '1G'}], 'component_id': 'urn:publicid:IDN+fms:psnc:serm:link', 'link_type': 'urn:felix', 'interface_ref': [{'component_id': '*'}, {'component_id': '*'}], 'component_manager_name': 'urn:publicid:IDN+fms:psnc:serm+authority+cm'}, {'property': [], 'component_id': 'urn:publicid:IDN+fms:psnc:serm+link+00:00:00:00:00:00:00:01_1_00:10:00:00:00:00:00:05_11', 'link_type': 'urn:felix+vlan_trans', 'interface_ref': [{'component_id': 'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1'}, {'component_id': 'urn:publicid:IDN+fms:psnc:tnrm+stp+urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_11'}], 'component_manager_name': None}, {'property': [], 'component_id': 'urn:publicid:IDN+fms:psnc:serm+link+00:00:00:00:00:00:00:01_3_00:10:00:00:00:00:00:05_12', 'link_type': 'urn:felix+vlan_trans', 'interface_ref': [{'component_id': 'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3'}, {'component_id': 'urn:publicid:IDN+fms:psnc:tnrm+stp+urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_12'}], 'component_manager_name': None}, {'property': [], 'component_id': 'urn:publicid:IDN+fms:psnc:serm+link+00:00:00:00:00:00:00:01_2_00:10:00:00:00:00:00:05_6', 'link_type': 'urn:felix+vlan_trans', 'interface_ref': [{'component_id': 'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2'}, {'component_id': 'urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_6'}], 'component_manager_name': None}, {'property': [], 'component_id': 'urn:publicid:IDN+fms:psnc:serm+link+00:00:00:00:00:00:00:01_4_00:10:00:00:00:00:00:05_7', 'link_type': 'urn:felix+vlan_trans', 'interface_ref': [{'component_id': 'urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4'}, {'component_id': 'urn:publicid:IDN+openflow:ocf:psnc:ofam+datapath+00:10:00:00:00:00:00:05_7'}], 'component_manager_name': None}]
    return all_links
  

def get_links_dict_for_rspec_teardown_function1():
    
    pass    

      
@with_setup(get_nodes_dict_for_rspec_setup_function, get_nodes_dict_for_rspec_teardown_function1)   
def test_node_generation_from_configuration():
    se_conf = SEConfigurator.seConfigurator("../../../../conf/se-config.yaml") # put testing conf to proper dir
    nodes = se_conf.get_nodes_dict_for_rspec()
    
    assert  nodes == all_nodes
    
@with_setup(get_links_dict_for_rspec_setup_function, get_links_dict_for_rspec_teardown_function1)   
def test_links_generation_from_configuration():
    se_conf = SEConfigurator.seConfigurator("../../../../conf/se-config_test.yaml") # put testing conf to proper dir
    links = se_conf.get_links_dict_for_rspec()
    
    assert  links == all_links

                 
                 
                 
                 
