from delegate.geni.v3.db_manager_se import db_sync_manager

import os
import yaml

class seConfigurator:
    def __init__(self,path=None):

        # read from config file
        current_path = os.path.dirname(os.path.abspath( __file__ ))
        if path is None:
            conf_file_path = os.path.join(current_path, "../../../../conf/se-config.yaml")
        else:
            conf_file_path = os.path.join(current_path, path)
        stream = open(conf_file_path, "r")
        initial_config = yaml.load(stream)
        self.configured_interfaces = self.convert_config_into_Resources_datamodel(initial_config["interfaces"])
        self.initial_configured_interfaces = initial_config["interfaces"]

        # Dynamic import of provisioning plugin (default: ryu_rest_of)
        try:
            self.provision_plugin = initial_config["provision_plugin"]
        except:
            self.provision_plugin = "ryu_rest_of"

        # Push port status from configuration file into SE-db
        # TODO: Add other rspec parameters to db
        db_sync_manager.update_resources(self.configured_interfaces, fromConfigFile=True)

        self.component_id_prefix = "urn:publicid:IDN+fms:" + initial_config["organisation"] + ":serm"
        self.component_manager_prefix = "urn:publicid:IDN+fms:" + initial_config["organisation"] + ":serm+authority+cm"
        self.vlan_trans = initial_config["vlan_trans"]
        self.qinq = initial_config["qinq"]
        self.capacity = initial_config["capacity"]
        self.dpid = initial_config["dpid"]

    def convert_config_into_Resources_datamodel(self, config):
        rm_datamodel = {}
        for interface in config:
            endpoints = config[interface]["remote_endpoints"]
            avail_vlans = {}
            for endpoint in endpoints:
                for vlan in endpoint["vlans"]:
                    if isinstance(vlan, int ):
                        avail_vlans[vlan] = True
                    else:
                        try:
                            v_start, v_end = vlan.split("-")
                            v_range = range(int(v_start), int(v_end)+1, 1)
                            for v in v_range:
                                avail_vlans[v] = True
                        except:
                            pass
            rm_datamodel[interface] = avail_vlans
        return rm_datamodel

    def get_provision_plugin(self):
        return self.provision_plugin

    def get_ports_configuration(self):
        return self.configured_interfaces

    def set_ports_configuration(self, config):
        self.configured_interfaces = config

    def get_concrete_port_status(self, port):
        return self.configured_interfaces[port]

    def set_concrete_port_status(self, port, vlan, status):
        self.configured_interfaces[port][vlan] = status

    def get_port_mapping(self):
        """Getting map of Felix urns and ports identifiers on SE"""
        component_id_prefix = self.component_id_prefix
        configured_interfaces = self.configured_interfaces
        portMapping = {}

        for iface in configured_interfaces:
            vlans_on_iface = configured_interfaces[iface]
            for vlan in vlans_on_iface:
                current_vlan_status = vlans_on_iface[vlan]
                available_iface = component_id_prefix + '+datapath+' + self.dpid + "_" + iface
                portMapping[available_iface] = iface

        return portMapping


    def check_available_resources(self, resources):

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        for resource in resources:
            try:
                r_splited = resource['port'].rsplit("_", 1)
                vlan = resource['vlan']
                component_id = r_splited[0]
                port = r_splited[1]
                vlans_result = self.get_concrete_port_status(port)
                result = vlans_result[vlan]
                # if (result is False) or (component_id != self.component_id_prefix):
                if (result is False) or (self.component_id_prefix not in resource["port"]):
                    return False
            except KeyError:
                return False
        return True

    def set_resource_reservation(self, resources):
        for resource in resources:
            r_splited = resource['port'].rsplit("_", 1)
            vlan = resource['vlan']
            port = r_splited[1]
            self.set_concrete_port_status(port, vlan, False)
            
        # Update the SE-db
        db_sync_manager.update_resources(self.configured_interfaces)

    def free_resource_reservation(self, resources):
        for resource in resources:
            r_splited = resource['port'].rsplit("_", 1)
            vlan = resource['vlan']
            port = r_splited[1]
            self.set_concrete_port_status(port, vlan, True)
            
        # Update the SE-db
        db_sync_manager.update_resources(self.configured_interfaces)


    def get_nodes_dict_for_rspec(self, geni_available):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        configured_interfaces = self.configured_interfaces

        nodes = [
            {
                'component_manager_id': component_manager_prefix,
                'exclusive':'false',
                'interfaces': [],
#                'component_id': component_id_prefix,
                'component_id': component_id_prefix + '+datapath+' + self.dpid,
                'sliver_type_name':None
            }
        ]

        # Prepare nodes
        for iface in configured_interfaces:
            vlans_on_iface = configured_interfaces[iface]
            for vlan in vlans_on_iface:
                current_vlan_status = vlans_on_iface[vlan]
                if current_vlan_status is not False or geni_available is False:
                    available_iface = {
                        'component_id': component_id_prefix + '+datapath+' + self.dpid + "_" + iface,
                        'vlan':[
                        ]
                    }
                    nodes[0]['interfaces'].append(available_iface)
                    break

        return nodes

    def get_links_dict_for_rspec(self, geni_available):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix

        # get data from db - TODO: refactor into function
        self.configured_interfaces = db_sync_manager.get_resources()

        configured_interfaces = self.configured_interfaces
        vlan_trans = self.vlan_trans
        qinq = self.qinq
        capacity = self.capacity

        # Prepare link capability translations
        # TODO: Check if this should provide VLAN trans params or not
        link_trans_capability = 'urn:felix'

        links_se = [
            {
                'component_id': component_id_prefix + ':link',
                'component_manager_name': component_manager_prefix,
                'interface_ref':[
                    {
                        'component_id':'*'
                    },
                    {
                        'component_id':'*'
                    }
                ],
                'property':[
                    {
                        'source_id':'*',
                        'dest_id':'*',
                        'capacity': capacity
                    }
                ],
                'link_type': link_trans_capability
            }
        ]

        # Prepare links
        config = self.initial_configured_interfaces
        for interface in config:
            endpoints = config[interface]["remote_endpoints"]
            for endpoint in endpoints:
                found = False
                for vlan in endpoint["vlans"]:
                    if found == False:
                        if isinstance(vlan, int ):
                            if configured_interfaces[interface][str(vlan)] == True or geni_available is False:
                                new_static_link =  {
                                    'component_id':component_id_prefix + '+link+' + self.dpid + "_" + interface + "_" + endpoint["name"].rsplit("+", 1)[1],
                                    'component_manager_name': component_id_prefix + "+authority+cm",
                                    'interface_ref':[
                                        {
                                            'component_id': component_id_prefix + '+datapath+' + self.dpid + "_" + interface
                                        },
                                        {
                                            'component_id': endpoint["name"]
                                        }
                                    ],
                                    'property':[

                                    ],
                                    'link_type':'urn:felix+' + endpoint["type"]
                                }
                                links_se.append(new_static_link)
                                found = True
                                break
                        else:
                            try:
                                v_start, v_end = vlan.split("-")
                                v_range = range(int(v_start), int(v_end)+1, 1)
                                for v in v_range:
                                    if configured_interfaces[interface][str(v)] == True or geni_available is False:
                                        new_static_link =  {
                                            'component_id':component_id_prefix + '+link+' + self.dpid + "_" + interface + "_" + endpoint["name"].rsplit("+", 1)[1],
                                            'component_manager_name': component_id_prefix + "+authority+cm",
                                            'interface_ref':[
                                                {
                                                    'component_id': component_id_prefix + '+datapath+' + self.dpid + "_" + interface
                                                },
                                                {
                                                    'component_id': endpoint["name"]
                                                }
                                            ],
                                            'property':[

                                            ],
                                            'link_type':'urn:felix+' + endpoint["type"]
                                        }
                                        links_se.append(new_static_link)
                                        found = True
                                        break
                            except:
                                pass

        return links_se
