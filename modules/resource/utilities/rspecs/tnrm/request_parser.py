from rspecs.parser_base import ParserBase
from rspecs.commons_tn import Node, Link, Interface


class TNRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3RequestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')

    def get_nodes(self, rspec):
        nodes = []
        for n in rspec.findall(".//{%s}node" % (self.none)):
            exclusive = None
            sliver = n.find("{%s}sliver_type" % (self.none))
            if sliver is not None:
                # for TNRM request the sliver tag MUST be empty
                # so this node is NOT a TN resource!
                continue

            n = Node(n.attrib.get("client_id"),
                      n.attrib.get("component_manager_id"),
                      n.attrib.get("exclusive"), exclusive)

            for i in n.iterfind("{%s}interface" % (self.none)):
                interface = Interface(i.attrib.get("client_id"))
                for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                    interface.add_vlan(sv.attrib.get("vlantag"),
                                sv.attrib.get("name"))
                n.add_interface(interface.serialize())

            nodes.append(n.serialize())
        return nodes

    def nodes(self):
        return self.get_nodes(self.rspec)

    def get_links(self, rspec):
        links_ = []
        for l in rspec.findall(".//{%s}link" % (self.none)):
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

            links_.append(l_.serialize())

        return links_

    def links(self):
        return self.get_links(self.rspec)