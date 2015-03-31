EMULAB_XMLNS = "http://www.protogeni.net/resources/rspec/ext/emulab/1"


# COM Data Models
class Node(object):
    # Node "unavailable" unless the contrary is said
    def __init__(self, component_id, component_manager_id, component_name,
                 exclusive=None, available=False, interfaces=[],
                 component_manager_uuid=None):
        self.__dict__.update({"component_id": component_id,  # Server / Node
                              "component_manager_id": component_manager_id,
                              "component_name": component_name,
                              "component_manager_uuid": component_manager_uuid,
                              "exclusive": exclusive,
                              "available": available,
                              "interfaces": interfaces})

    def add_component_manager_uuid(self, cm_uuid):
        self.component_manager_uuid = cm_uuid

    def add_interface(self, interface):
        if interface not in self.interfaces:
            self.interfaces.append(interface)

    def clear_interfaces(self):
        self.interfaces = []

    def serialize(self):
        return self.__dict__


class Sliver(Node):
    """
    Extends Node information for practical purposes.
    """
    def __init__(self, component_manager_id, component_id, client_id,
                 exclusive=False, available=False, sliver_type="emulab-xen",
                 disk_image="default", ram="512", disk="8", cores="1"):
        super(Sliver, self).__init__(component_id, component_id,
                                     component_manager_id, exclusive,
                                     available)
        # Extend internal dictionary
        self.__dict__.update({"client_id": client_id,
                              "sliver_type": sliver_type,
                              "disk_image": disk_image,
                              "ram": ram,
                              "disk": disk,
                              "cores": cores})

    def add_sliver_id(self, sliver_id):
        self.__dict__.update({"sliver_id": sliver_id})

    def serialize(self):
        return self.__dict__


class Link(object):
    def __init__(self, component_id, component_name, link_type="",
                 component_manager_uuid=None):
        self.__dict__.update({"component_id": component_id,
                              "component_name": component_name,
                              "component_manager_uuid": component_manager_uuid,
                              "links": [],
                              "link_type": link_type})

    def add_component_manager_uuid(self, cm_uuid):
        self.component_manager_uuid = cm_uuid

    def add_link(self, source, dest, capacity):
        self.links.append(
            {"source_id": source, "dest_id": dest, "capacity": capacity})

    def add_type(self, link_type):
        self.link_type = link_type

    def serialize(self):
        return self.__dict__


class COMNode(object):
    def __init__(self, client_id, component_id, component_manager_id,
                 sliver_id, component_manager_uuid=None):
        self.node = {'client_id': client_id,
                     'component_id': component_id,
                     'component_manager_id': component_manager_id,
                     'component_manager_uuid': component_manager_uuid,
                     'sliver_id': sliver_id,
                     'sliver_type_name': None,
                     'services': []}

    def sliver_type(self, name):
        self.node['sliver_type_name'] = name

    def add_service(self, auth, hostname, port, username, pswd=None):
        login = {'authentication': auth,
                 'hostname': hostname,
                 'port': port,
                 'username': username,
                 'password': pswd}
        self.node['services'].append({'login': login})

    def add_component_manager_uuid(self, cm_uuid):
        self.node['component_manager_uuid'] = cm_uuid

    def serialize(self):
        return self.node
