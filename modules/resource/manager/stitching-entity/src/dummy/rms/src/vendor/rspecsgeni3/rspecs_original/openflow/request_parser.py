from rspecs.commons_of import Datapath, Match, DEFAULT_OPENFLOW
from rspecs.parser_base import ParserBase


class OFv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(OFv3RequestParser, self).__init__(from_file, from_string)
        self.__of = self.rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW

    def sliver(self):
        s = self.__find_sliver()
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}

    def controllers(self):
        return [{"url": c.attrib.get("url"), "type": c.attrib.get("type")}
                for c in self.__find_controllers()]

    def groups(self):
        return [{"name": g.attrib.get("name")}
                for g in self.__find_groups()]

    def datapaths(self, group_name):
        g = self.__find_group(group_name)
        return [self.__datapath(dp)
                for dp in g.iterfind("{%s}datapath" % (self.__of))]

    def matches(self):
        matches_ = []
        for m in self.__find_matches():
            m_ = Match()
            [m_.add_use_group(ug.attrib.get("name"))
             for ug in m.iterfind("{%s}use-group" % (self.__of))]

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
            matches_.append(m_.serialize())
        return matches_

    def __find_sliver(self):
        sliver = self.rspec.find("{%s}sliver" % (self.__of))
        if sliver is None:
            self.raise_exception("Sliver tag not found!")
        return sliver

    def __find_controllers(self):
        return self.rspec.findall(".//{%s}controller" % (self.__of))

    def __find_group(self, name):
        groups = self.rspec.findall(".//{%s}group" % (self.__of))
        for group in groups:
            if group.get("name") == name:
                return group
        self.raise_exception("Group %s not found!" % (name))

    def __find_groups(self):
        return self.rspec.findall(".//{%s}group" % (self.__of))

    def __find_matches(self):
        return self.rspec.findall(".//{%s}match" % (self.__of))

    def __datapath(self, element):
        d = Datapath(element.attrib.get("component_id"),
                     element.attrib.get("component_manager_id"),
                     element.attrib.get("dpid"))
        for p in element.iterfind("{%s}port" % (self.__of)):
            d.add_port(p.attrib.get("num"), p.attrib.get("name"))
        return d.serialize()

    def __packet(self, element, tag):
        value = element.find("{%s}%s" % (self.__of, tag))
        if value is not None:
            return value.attrib.get("value")
        return None
