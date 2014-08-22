from delegate.geni.v3.rspecs.commons import Match, Datapath, OFGroup
from lxml import etree


class RORequestParser(object):
    def __init__(self, from_file=None, from_string=None):
        if from_file is not None:
            self.__rspec = etree.parse(from_file).getroot()
        elif from_string is not None:
            self.__rspec = etree.fromstring(from_string)

        self.__of = self.__rspec.nsmap.get('openflow')
        self.__none = self.__rspec.nsmap.get(None)

    def of_sliver(self):
        s = self.__rspec.find("{%s}sliver" % (self.__of))
        if s is None:
            return None
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}

    def of_controllers(self):
        return [
            {"url": c.attrib.get("url"), "type": c.attrib.get("type")}
            for c in self.__rspec.findall(".//{%s}controller" % (self.__of))]

    def of_groups(self):
        groups = []
        for group in self.__rspec.findall(".//{%s}group" % (self.__of)):
            g = OFGroup(group.get('name'))
            for dp in group.iterfind("{%s}datapath" % (self.__of)):
                g.add_datapath(self.__datapath(dp))

            groups.append(g.serialize())
        return groups

    def of_matches(self):
        matches = []
        for match in self.__rspec.findall(".//{%s}match" % (self.__of)):
            m = Match()
            for ug in match.iterfind("{%s}use-group" % (self.__of)):
                m.add_use_group(ug.attrib.get("name"))

            for dp in match.iterfind("{%s}datapath" % (self.__of)):
                m.add_datapath(self.__datapath(dp))

            packet = match.find("{%s}packet" % (self.__of))
            if packet is not None:
                dl_src = self.__packet(packet, "dl_src")
                dl_dst = self.__packet(packet, "dl_dst")
                dl_type = self.__packet(packet, "dl_type")
                dl_vlan = self.__packet(packet, "dl_vlan")
                nw_src = self.__packet(packet, "nw_src")
                nw_dst = self.__packet(packet, "nw_dst")
                nw_proto = self.__packet(packet, "nw_proto")
                tp_src = self.__packet(packet, "tp_src")
                tp_dst = self.__packet(packet, "tp_dst")

                m.set_packet(dl_src, dl_dst, dl_type, dl_vlan,
                             nw_src, nw_dst, nw_proto, tp_src, tp_dst)

            matches.append(m.serialize())
        return matches

    def get_rspec(self):
        return self.__rspec

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)

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
