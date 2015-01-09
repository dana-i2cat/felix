import yaml

class seConfigurator:
    def __init__(self):

        stream = open("../conf/se-config.yaml", 'r')
        initial_config = yaml.load(stream)
        self.configured_interfaces = initial_config["interfaces"]
        self.component_id_prefix = initial_config["component_id"]
        self.component_manager_prefix = initial_config["component_manager_id"]
        self.configured_interfaces = initial_config["interfaces"]
        self.vlan_trans = initial_config["vlan_trans"]
        self.qinq = initial_config["qinq"]
        self.capacity = initial_config["capacity"]

    def get_ports_configuration(self):
        return self.configured_interfaces

    def set_ports_configuration(self, config):
        self.configured_interfaces = config

    def get_concrete_port_status(self, port):
        return self.configured_interfaces[port]

    def set_concrete_port_status(self, port, vlan, status):
        self.configured_interfaces[port][vlan] = status

    def check_available_resources(self, resources):
        for resource in resources:
            try:
                r_splited = resource['port'].rsplit(":", 1)
                vlan = resource['vlan']
                component_id = r_splited[0]
                port = r_splited[1]
                vlans_result = self.get_concrete_port_status(port)
                result = vlans_result[int(vlan)] # rspec contains vlan as string value
                if (result is False) or (component_id != self.component_id_prefix):
                    return False
            except KeyError:
                return False
        return True

    def set_resource_reservation(self, resources):
        for resource in resources:
            r_splited = resource['port'].rsplit(":", 1)
            vlan = resource['vlan']
            port = r_splited[1]
            self.set_concrete_port_status(port, int(vlan), False)


    def get_nodes_dict_for_rspec(self):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix
        configured_interfaces = self.configured_interfaces
        vlan_trans = self.vlan_trans
        qinq = self.qinq

        # Prepare link capability translations
        link_trans_capability = 'urn:felix'
        if vlan_trans:
            link_trans_capability += '+vlan_trans'
        if qinq:
            link_trans_capability += '+QinQ'

        nodes = [
            {
                'component_manager_id': component_manager_prefix,
                'exclusive':'false',
                'interfaces':[],
                'component_id': component_id_prefix,
                'sliver_type_name':None
            }
        ]

        # Prepare nodes
        for iface in configured_interfaces:
            vlans_on_iface = configured_interfaces[iface]
            for vlan in vlans_on_iface:
                current_vlan_status = vlans_on_iface[vlan]
                if current_vlan_status is not False:
                    available_iface = {
                        'component_id': component_id_prefix + ':' + iface,
                        'vlan':[
                        ]
                    }
                    nodes[0]['interfaces'].append(available_iface)
                    break

        return nodes

    def get_links_dict_for_rspec(self):
        component_id_prefix = self.component_id_prefix
        component_manager_prefix = self.component_manager_prefix
        configured_interfaces = self.configured_interfaces
        vlan_trans = self.vlan_trans
        qinq = self.qinq
        capacity = self.capacity

        # Prepare link capability translations
        link_trans_capability = 'urn:felix'
        if vlan_trans:
            link_trans_capability += '+vlan_trans'
        if qinq:
            link_trans_capability += '+QinQ'

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
        for iface in configured_interfaces:
            links = configured_interfaces[iface]
            # Check if links is VLAN or static
            for link in links:
                link_type = links[link]
                if link_type is True:
                    print "Found VLAN: ", link
                elif link_type is not True and link_type is not False:
                    print "Found static link: ", link
                    remote_endpoint = link_type
                    print remote_endpoint

                    new_static_link =  {
                        'component_id':'urn:publicid:aist-se1-' + link,
                        'component_manager_name':None,
                        'interface_ref':[
                            {
                                'component_id': component_id_prefix + ':' + iface
                            },
                            {
                                'component_id': remote_endpoint
                            }
                        ],
                        'property':[

                        ],
                        'link_type':'urn:felix+static_link'
                    }

                    links_se.append(new_static_link)

        return links_se