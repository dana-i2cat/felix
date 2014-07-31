DEFAULT_XMLNS = "http://www.geni.net/resources/rspec/3"
DEFAULT_XS = "http://www.w3.org/2001/XMLSchema-instance"
DEFAULT_OPENFLOW = "http://www.geni.net/resources/rspec/ext/openflow/3"

DSL_PREFIX = "http://www.geni.net/resources/rspec/"
DEFAULT_SCHEMA_LOCATION = DSL_PREFIX + "3 "
DEFAULT_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3 "

CONTROLLER_TYPE_PRIMARY = "primary"
CONTROLLER_TYPE_MONITOR = "monitor"
CONTROLLER_TYPE_BACKUP = "backup"

NODE_OPENFLOW = "openflow-switch"


class Datapath(object):
    def __init__(self, component_id, component_manager_id, dpid):
        self.component_id = component_id
        self.component_manager_id = component_manager_id
        self.dpid = dpid
        self.ports = []

    def add_port(self, num, name=None):
        self.ports.append({'num': str(num), 'name': name})

    def __repr__(self):
        return "id: %s, manager_id: %s, dpid: %s, ports: %s" %\
               (self.component_id, self.component_manager_id,
                self.dpid, self.ports)


class Match(object):
    def __init__(self):
        self.use_groups = []
        self.datapaths = []
        self.packet = None

    def add_use_group(self, name):
        self.use_groups.append({'name': name})

    def add_datapath(self, dpath):
        self.datapaths.append({'datapath': dpath})

    def set_packet(self, dl_src=None, dl_dst=None, dl_type=None, dl_vlan=None,
                   nw_src=None, nw_dst=None, nw_proto=None,
                   tp_src=None, tp_dst=None):
        self.packet = {'dl_src': dl_src,
                       'dl_dst': dl_dst,
                       'dl_type': dl_type,
                       'dl_vlan': dl_vlan,
                       'nw_src': nw_src,
                       'nw_dst': nw_dst,
                       'nw_proto': nw_proto,
                       'tp_src': tp_src,
                       'tp_dst': tp_dst}

    def __repr__(self):
        return "use_groups: %s, datapaths: %s, packet: %s" %\
               (self.use_groups, self.datapaths, self.packet)


class Node(object):
    def __init__(self, id, manager_id, name, exclusive,
                 hardware_type, available):
        self.component_id = id
        self.component_manager_id = manager_id
        self.component_name = name
        self.exclusive = exclusive
        self.hardware_type_name = hardware_type
        self.available_now = available

    def node_to_string(self):
        return "id: %s, manager_id: %s, name: %s, exclusive: %s, " +\
               "hardware_type: %s, available" %\
               (self.component_id, self.component_manager_id,
                self.component_name, self.exclusive, self.hardware_type_name,
                self.available_now)


class OpenFlowNode(Node):
    def __init__(self, component_id, component_manager_id, dpid,
                 exclusive, available):
        super(OpenFlowNode, self).__init__(component_id, component_manager_id,
                                           dpid, exclusive, NODE_OPENFLOW,
                                           available)
        self.dpid = dpid
        self.ports = []

    def add_port(self, num, name=None):
        self.ports.append({'num': str(num), 'name': name})

    def __repr__(self):
        return "node: %s, dpid: %s, ports: %s" %\
               (self.node_to_string(), self.dpid, self.ports)
