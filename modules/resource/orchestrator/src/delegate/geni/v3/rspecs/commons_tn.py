DEFAULT_TN = "http://www.geni.net/resources/rspec/ext/tn/3"
DEFAULT_SHARED_VLAN = "http://www.geni.net/resources/rspec/ext/shared-vlan/1"


# TN Data Models
class Interface(object):
    def __init__(self, component_id):
        self.interface = {'component_id': component_id,
                          'vlan': []}

    def add_vlan(self, tag, name=None, descr=None):
        v = {'tag': tag}
        if name is not None:
            v['name'] = name
        if descr is not None:
            v['description'] = descr

        self.interface['vlan'].append(v)

    def serialize(self):
        return self.interface


class Node(object):
    def __init__(self, component_id, component_manager_id, exclusive,
                 sliver_type_name):
        self.node = {'component_id': component_id,
                     'component_manager_id': component_manager_id,
                     'exclusive': exclusive,
                     'sliver_type_name': sliver_type_name,
                     'interfaces': []}

    def add_interface(self, intf):
        self.node['interfaces'].append(intf)

    def serialize(self):
        return self.node


class Link(object):
    def __init__(self, component_id, component_manager_name):
        self.link = {'component_id': component_id,
                     'component_manager_name': component_manager_name,
                     'interface_ref': [],
                     'property': []}

    def add_interface_ref(self, cid):
        self.link['interface_ref'].append({'component_id': cid})

    def add_property(self, source, dest, capacity):
        self.link['property'].append(
            {'source_id': source, 'dest_id': dest, 'capacity': str(capacity)})

    def serialize(self):
        return self.link
