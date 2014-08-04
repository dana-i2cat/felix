from commons import Datapath, Match
from delegate.geni.v3 import exceptions
from lxml import etree

class OFv3RequestParser(object):
    def __init__(self, ingress):
        self.__rspec = etree.parse(ingress)
        self.__openflow = self.__rspec.getroot().nsmap.get('openflow')

    def sliver(self):
        sliver_ = {"description": None,
                   "ref": None,
                   "email": None}
        s = self.__find_sliver()
        if s.attrib.get("description") is not None:
            sliver_["description"] = s.attrib.get("description")
        if s.attrib.get("ref") is not None:
            sliver_["ref"] = s.attrib.get("ref")
        if s.attrib.get("email") is not None:
            sliver_["email"] = s.attrib.get("email")
        return sliver_

    def controllers(self):
        return [{"url": c.attrib.get("url"), "type": c.attrib.get("type")}
                for c in self.__find_controllers()]

    def groups(self):
        return [{"name": g.attrib.get("name")}
                for g in self.__find_groups()]

    def datapaths(self, group_name):
        g = self.__find_group(group_name)
        return [{"datapath": self.__datapath(dp)}
                for dp in g.iterfind("{%s}datapath" % (self.__openflow))]

    def matches(self):
        matches_ = []
        for m in self.__find_matches():
            m_ = Match()
            [m_.add_use_group(ug.attrib.get("name"))
             for ug in m.iterfind("{%s}use-group" % (self.__openflow))]

            for dp in m.iterfind("{%s}datapath" % (self.__openflow)):
                m_.add_datapath(self.__datapath(dp))

            packet_ = m.find("{%s}packet" % (self.__openflow))
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
            matches_.append({"match": m_})
        return matches_

    def get_rspec(self):
        return self.__rspec.getroot()

    def __find_sliver(self):
        sliver = self.__rspec.find("{%s}sliver" % (self.__openflow))
        if sliver is None:
            raise exceptions.RSpecError("Sliver tag not found!")
        return sliver

    def __find_controllers(self):
        # using xpath recursive
        return self.__rspec.findall(".//{%s}controller" % (self.__openflow))

    def __find_group(self, name):
        groups = self.__rspec.findall(".//{%s}group" % (self.__openflow))
        for group in groups:
            if group.get("name") == name:
                return group
        raise exceptions.RSpecError("Group %s not found!" % (name))

    def __find_groups(self):
        return self.__rspec.findall(".//{%s}group" % (self.__openflow))

    def __find_matches(self):
        return self.__rspec.findall(".//{%s}match" % (self.__openflow))

    def __datapath(self, element):
        d = Datapath(element.attrib.get("component_id"),
                     element.attrib.get("component_manager_id"),
                     element.attrib.get("dpid"))
        for p in element.iterfind("{%s}port" % (self.__openflow)):
            d.add_port(p.attrib.get("num"), p.attrib.get("name"))
        return d

    def __packet(self, element, tag):
        value = element.find("{%s}%s" % (self.__openflow, tag))
        if value is not None:
            return value.attrib.get("value")
        return None

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
