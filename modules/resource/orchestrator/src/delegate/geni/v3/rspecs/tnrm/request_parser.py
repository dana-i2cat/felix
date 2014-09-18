from delegate.geni.v3.rspecs.parser_base import ParserBase
from delegate.geni.v3.rspecs.commons_tn import Node, Link


class TNRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3RequestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')

    def __interface_details(self, node, interface_tag):
        ip_tag = interface_tag.find("{%s}ip" % (self.none))
        if ip_tag is None:
            node.add_interface(interface_tag.attrib.get("client_id"))
        else:
            node.add_interface(interface_tag.attrib.get("client_id"),
                               ip_tag.attrib.get("address"),
                               ip_tag.attrib.get("netmask"),
                               ip_tag.attrib.get("type"))

    def nodes(self):
        nodes_ = []
        for n in self.rspec.findall(".//{%s}node" % (self.none)):
            sliver_ = n.find("{%s}sliver_type" % (self.none))
            if sliver_ is None:
                self.raise_exception("Sliver-Type tag not found in node!")

            n_ = Node(n.attrib.get("client_id"),
                      n.attrib.get("component_manager_id"),
                      n.attrib.get("exclusive"),
                      sliver_.attrib.get("name"))

            [self.__interface_details(n_, i)
             for i in n.iterfind("{%s}interface" % (self.none))]

            nodes_.append(n_.serialize())

        return nodes_

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            l_ = Link(l.attrib.get("client_id"), manager_.attrib.get("name"))

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            sv_ = l.find("{%s}link_shared_vlan" % (self.__sv))
            if sv_ is None:
                self.raise_exception("Shared-Vlan tag not found in link!")

            l_.add_shared_vlan(sv_.attrib.get("name"),
                               sv_.attrib.get("vlanTag"))

            links_.append(l_.serialize())

        return links_
