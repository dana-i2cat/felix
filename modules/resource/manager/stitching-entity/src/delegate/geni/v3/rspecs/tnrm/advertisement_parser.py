from delegate.geni.v3.rspecs.parser_base import ParserBase
from delegate.geni.v3.rspecs.commons_tn import Node, Interface, Link


class TNRMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3AdvertisementParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')

    def nodes(self):
        nodes_ = []
        for n in self.rspec.iterchildren("{%s}node" % (self.none)):
            s_ = None
            sliver_type = n.find("{%s}sliver_type" % (self.none))
            if sliver_type is not None:
                s_ = sliver_type.attrib.get("name")

            n_ = Node(n.attrib.get("component_id"),
                      n.attrib.get("component_manager_id"),
                      n.attrib.get("exclusive"), s_)

            for i in n.iterfind("{%s}interface" % (self.none)):
                i_ = Interface(i.attrib.get("component_id"))
                for v in i.iterfind("{%s}available" % (self.__sv)):
                    i_.add_vlan(v.attrib.get("localTag"), v.attrib.get("name"),
                                v.attrib.get("description"))
                n_.add_interface(i_.serialize())

            nodes_.append(n_.serialize())

        return nodes_

    def links(self):
        links_ = []
        for l in self.rspec.iterchildren("{%s}link" % (self.none)):
            component_manager = l.find("{%s}component_manager" % (self.none))
            if component_manager is None:
                self.raise_exception("Component_manager tag not found!")

            l_ = Link(l.attrib.get("component_id"),
                      component_manager.attrib.get("name"))

            for ref in l.iterchildren("{%s}interface_ref" % (self.none)):
                l_.add_interface_ref(ref.attrib.get("component_id"))

            for p in l.iterchildren("{%s}property" % (self.none)):
                l_.add_property(p.attrib.get("source_id"),
                                p.attrib.get("dest_id"),
                                p.attrib.get("capacity"))

            links_.append(l_.serialize())

        return links_
