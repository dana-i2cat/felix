DEFAULT_SHARED_VLAN = "http://www.geni.net/resources/rspec/ext/shared-vlan/1"


# TN Data Models
class Node(object):
    def __init__(self, component_id, component_manager_id, exclusive,
                 sliver_type_name):
        self.node = {'component_id': component_id,
                     'component_manager_id': component_manager_id,
                     'exclusive': exclusive,
                     'sliver_type_name': sliver_type_name,
                     'interfaces': []}

    def add_interface(self, name, address, netmask, type):
        self.node['interfaces'].append(
            {'component_id': self.node.get('component_id') + ":" + name,
             'ip_address': address, 'ip_netmask': netmask, 'ip_type': type})

    def serialize(self):
        return self.node


class Link(object):
    def __init__(self, component_id, component_manager_name):
        self.link = {'component_id': component_id,
                     'component_manager_name': component_manager_name,
                     'interface_ref': [],
                     'property': [],
                     'shared_vlan': []}

    def add_interface_ref(self, cid):
        self.link['interface_ref'].append({'component_id': cid})

    def add_property(self, source, dest, capacity):
        self.link['property'].append(
            {'source_id': source, 'dest_id': dest, 'capacity': str(capacity)})

    def add_shared_vlan(self, name, descr, tag):
        self.link['shared_vlan'].append(
            {'name': name, 'description': descr, 'localTag': tag})

    def serialize(self):
        return self.link
