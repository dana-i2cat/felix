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

    def add_interface(self, name, address=None, netmask=None, typee=None):
        i = {'component_id': name}
        if address is not None:
            i['ip_address'] = address
        if netmask is not None:
            i['ip_netmask'] = netmask
        if typee is not None:
            i['ip_type'] = typee

        self.node['interfaces'].append(i)

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

    def add_shared_vlan(self, name, tag, descr=None):
        l = {'name': name, 'localTag': tag}
        if descr is not None:
            l['description'] = descr

        self.link['shared_vlan'].append(l)

    def serialize(self):
        return self.link
