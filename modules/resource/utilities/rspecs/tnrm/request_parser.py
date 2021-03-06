from rspecs.parser_base import ParserBase
from rspecs.commons_tn import Node, Link, Interface

import core
logger = core.log.getLogger("utility-rspec")


class TNRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3RequestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')
        self.__proto = self.rspec.nsmap.get('protogeni')

    def check_tn_node_resource(self, node):
        # according to the proposed URNs structure, a TN-node MUST have
        # "tnrm" as resource-name (client_id) and authority
        # (component_manager_id) fields
        # At least we verify the autority field here!
        if not node.attrib.get("component_manager_id"):
            return False
        if "tnrm" in node.attrib.get("component_manager_id"):
            return True
        return False

    def check_tn_link_resource(self, link, c_manager):
        # according to the proposed URNs structure, a TN-link MUST have
        # "tnrm" as resource-name (client_id) and authority
        # (component_manager_name) fields
        # At least we verify the autority field here!
        if not c_manager.attrib.get("name"):
            return False
        if "tnrm" in c_manager.attrib.get("name"):
            return True
        return False

    def update_protogeni_cm_uuid(self, tag, obj):
        cmuuid = tag.attrib.get("{%s}component_manager_uuid" % (self.__proto))
        if cmuuid is not None:
            obj.add_component_manager_uuid(cmuuid)

    def get_nodes(self, rspec):
        nodes = []
        for n in rspec.findall(".//{%s}node" % (self.none)):
            if not self.check_tn_node_resource(n):
                logger.info("Skipping this node, not a TN-res: %s", (n,))
                continue

            node = Node(n.attrib.get("client_id"),
                        n.attrib.get("component_manager_id"),
                        n.attrib.get("exclusive"))

            self.update_protogeni_cm_uuid(n, node)

            for i in n.iterfind("{%s}interface" % (self.none)):
                interface = Interface(i.attrib.get("client_id"))
                for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                    interface.add_vlan(sv.attrib.get("vlantag"),
                                       sv.attrib.get("name"))
                node.add_interface(interface.serialize())

            nodes.append(node.serialize())
        return nodes

    def nodes(self):
        return self.get_nodes(self.rspec)

    def get_links(self, rspec):
        links_ = []
        for l in rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            if not self.check_tn_link_resource(l, manager_):
                logger.info("Skipping this link, not a TN-res: %s", (l,))
                continue

            l_ = Link(l.attrib.get("client_id"), manager_.attrib.get("name"))

            self.update_protogeni_cm_uuid(l, l_)

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_

    def links(self):
        return self.get_links(self.rspec)
