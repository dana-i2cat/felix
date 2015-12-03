from rspecs.commons_of import Datapath, Match, Group, DEFAULT_OPENFLOW
from rspecs.parser_base import ParserBase


class OFv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(OFv3RequestParser, self).__init__(from_file, from_string)
        self.__of = self.rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW

    def get_sliver(self, rspec):
        s = self.__find_sliver(rspec)
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}

    def sliver(self):
        return self.get_sliver(self.rspec)

    def get_controllers(self, rspec):
        return [{"url": c.attrib.get("url"), "type": c.attrib.get("type")}
                for c in self.__find_controllers(rspec)]

    def controllers(self):
        return self.get_controllers(self.rspec)

    def get_groups(self, rspec):
        groups = []
        for group in self.__find_groups(rspec):
            g = self.format_group(group)
            groups.append(g.serialize())
        return groups

    def groups(self):
        return self.get_groups(self.rspec)

    def format_group(self, group):
        g = Group(group.get('name'))
        for dp in group.iterfind("{%s}datapath" % (self.__of)):
            g.add_datapath(self.__datapath(dp))
        return g

    def datapaths(self, group_name):
        g = self.__find_group(group_name)
        return [self.__datapath(dp)
                for dp in g.iterfind("{%s}datapath" % (self.__of))]

    def get_matches(self, rspec):
        matches_ = []
        for m in self.__find_matches(rspec):
            m_ = self.format_match(m)
            matches_.append(m_.serialize())
        return matches_

    def matches(self):
        return self.get_matches(self.rspec)

    def format_match(self, m):
        m_ = Match()
        for ug in m.iterfind("{%s}use-group" % (self.__of)):
            m_.add_use_group(ug.attrib.get("name"))

        for dp in m.iterfind("{%s}datapath" % (self.__of)):
            m_.add_datapath(self.__datapath(dp))

        packet_ = m.find("{%s}packet" % (self.__of))
        if packet_ is not None:
            dl_src = self.__packet(packet_, "dl_src")
            dl_dst = self.__packet(packet_, "dl_dst")
            dl_type = self.__packet(packet_, "dl_type")
            dl_vlan = self.__packet(packet_, "dl_vlan")
            nw_src = self.__packet(packet_, "nw_src")
            nw_dst = self.__packet(packet_, "nw_dst")
            nw_proto = self.__packet(packet_, "nw_proto")
            tp_src = self.__packet(packet_, "tp_src")
            tp_dst = self.__packet(packet_, "tp_dst")

            m_.set_packet(dl_src, dl_dst, dl_type, dl_vlan,
                          nw_src, nw_dst, nw_proto, tp_src, tp_dst)
        return m_

    def get_groups_matches(self, rspec):
        groups = rspec.findall(".//{%s}group" % (self.__of))
        groups_matches = []
        for group in groups:
            group_f = self.format_group(group).group
            matches = group.getparent().findall(".//{%s}match" % (self.__of))
            matches_f = [ self.format_match(m).match for m in matches ]
            groups_matches.append({ "group": group_f, "match": matches_f })
        return groups_matches

    def groups_matches(self):
        return self.get_groups_matches(self.rspec)

    def __find_sliver(self, rspec):
        sliver = rspec.find("{%s}sliver" % (self.__of))
        if sliver is None:
            self.raise_exception("Sliver tag not found!")
        return sliver

    def __find_controllers(self, rspec):
        return rspec.findall(".//{%s}controller" % (self.__of))

    def __find_groups(self, rspec):
        return rspec.findall(".//{%s}group" % (self.__of))

    def __find_group(self, name):
        groups = self.rspec.findall(".//{%s}group" % (self.__of))
        for group in groups:
            if group.get("name") == name:
                return group
        self.raise_exception("Group %s not found!" % (name))

    def __find_matches(self, rspec):
        return rspec.findall(".//{%s}match" % (self.__of))

    def __datapath(self, element):
        d = Datapath(element.attrib.get("component_id"),
                     element.attrib.get("component_manager_id"),
                     element.attrib.get("dpid"))
        for p in element.iterfind("{%s}port" % (self.__of)):
            d.add_port(p.attrib.get("num"), p.attrib.get("name"))
        return d.serialize()

    def __packet(self, element, tag):
        value = element.find("{%s}%s" % (self.__of, tag))
        return value.attrib.get("value") if (value is not None) else None
