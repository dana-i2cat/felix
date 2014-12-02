EMULAB_XMLNS = "http://www.protogeni.net/resources/rspec/ext/emulab/1"

# COM Data Models
class Node(object):
    # Node "unavailable" unless the contrary is said
    def __init__(self, component_id, component_manager_id, component_name,
                 exclusive=None, available=False, interfaces=[]):
        self.__dict__.update({
                     "component_id": component_id, # Server / Node
                     "component_manager_id": component_manager_id, # CRM
                     "component_name": component_name,
                     "exclusive": exclusive,
                     "available": available,
                     "interfaces": interfaces
                    })

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
        super(Sliver, self).__init__(component_id, component_id, component_manager_id,
                                exclusive, available)
        # Extend internal dictionary
        self.__dict__.update({
                        "client_id": client_id,
                        "sliver_type": sliver_type,
                        "disk_image": disk_image,
                        "ram": ram,
                        "disk": disk,
                        "cores": cores,
                        })

    def add_sliver_id(self, sliver_id):
        self.__dict__.update({
                                "sliver_id": sliver_id,
                            })

    def serialize(self):
        return self.__dict__


class Link(object):
    def __init__(self, component_id, component_name, link_type=""):
        self.__dict__.update({
                     "component_id": component_id,
                     "component_name": component_name,
                     "links": [],
                     "link_type": link_type,
                    })

    def add_link(self, source, dest, capacity):
        self.links.append(
            {"source_id": source, "dest_id": dest, "capacity": capacity})

    def add_type(self, link_type):
        self.link_type = link_type

    def serialize(self):
        return self.__dict__

