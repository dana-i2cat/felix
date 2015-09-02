from commons import DSL_PREFIX, DEFAULT_SCHEMA_LOCATION

DEFAULT_OPENFLOW = "http://www.geni.net/resources/rspec/ext/openflow/3"
DEFAULT_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3 "

CONTROLLER_TYPE_PRIMARY = "primary"
CONTROLLER_TYPE_MONITOR = "monitor"
CONTROLLER_TYPE_BACKUP = "backup"

NODE_OPENFLOW = "openflow-switch"


# OF Data Models
class Datapath(object):
    def __init__(self, component_id, component_manager_id, dpid):
        self.datapath = {'component_id': component_id,
                         'component_manager_id': component_manager_id,
                         'dpid': dpid,
                         'ports': []}

    def add_port(self, num, name=None):
        self.datapath['ports'].append({'num': str(num), 'name': name})

    def serialize(self):
        return self.datapath


class Match(object):
    def __init__(self):
        self.match = {'use_groups': [],
                      'dpids': [],
                      'packet': None}

    def add_use_group(self, name):
        self.match['use_groups'].append({'name': name})

    def add_datapath(self, dpath):
        self.match['dpids'].append(dpath)

    def set_packet(self, dl_src=None, dl_dst=None, dl_type=None, dl_vlan=None,
                   nw_src=None, nw_dst=None, nw_proto=None,
                   tp_src=None, tp_dst=None):
        self.match['packet'] = {'dl_src': dl_src,
                                'dl_dst': dl_dst,
                                'dl_type': dl_type,
                                'dl_vlan': dl_vlan,
                                'nw_src': nw_src,
                                'nw_dst': nw_dst,
                                'nw_proto': nw_proto,
                                'tp_src': tp_src,
                                'tp_dst': tp_dst}

    def serialize(self):
        return self.match


class Link(object):
    def __init__(self, component_id):
        self.link = {'component_id': component_id,
                     'dpids': [],
                     'ports': []}

    def add_datapath(self, dpath):
        self.link['dpids'].append(dpath)

    def add_port(self, pnum):
        self.link['ports'].append({'port_num': str(pnum)})

    def serialize(self):
        return self.link


class Group(object):
    def __init__(self, name):
        self.group = {'name': name,
                      'dpids': []}

    def add_datapath(self, dpath):
        self.group['dpids'].append(dpath)

    def serialize(self):
        return self.group


class OFSliver(object):
    def __init__(self, description, email, status, urn):
        self.sliver = {'description': description,
                       'email': email,
                       'status': status,
                       'urn': urn}

    def serialize(self):
        return self.sliver
