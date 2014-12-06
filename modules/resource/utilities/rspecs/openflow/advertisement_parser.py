from rspecs.commons import FEDLink
from rspecs.commons_of import Datapath, Link, DEFAULT_OPENFLOW
from rspecs.parser_base import ParserBase


class OFv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(OFv3AdvertisementParser, self).__init__(from_file, from_string)
        self.__of = self.rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW

    def datapaths(self):
        ofdps_ = []
        for ofd in self.rspec.iterchildren("{%s}datapath" % (self.__of)):
            of_ = Datapath(ofd.attrib.get("component_id"),
                           ofd.attrib.get("component_manager_id"),
                           ofd.attrib.get("dpid"))

            [of_.add_port(p.attrib.get("num"), p.attrib.get("name"))
             for p in ofd.findall(".//{%s}port" % (self.__of))]

            ofdps_.append(of_.serialize())
        return ofdps_

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            if l.find(".//{%s}datapath" % (self.__of)) is not None:
                of_ = Link(l.attrib.get("component_id"))
                for dpid in l.iterchildren("{%s}datapath" % (self.__of)):
                    d = Datapath(dpid.attrib.get("component_id"),
                                 dpid.attrib.get("component_manager_id"),
                                 dpid.attrib.get("dpid"))
                    of_.add_datapath(d.serialize())

                for port in l.iterchildren("{%s}port" % (self.__of)):
                    of_.add_port(port.attrib.get("port_num"))

            elif l.find(".//{%s}interface_ref" % (self.none)) is not None:
                of_ = FEDLink(l.attrib.get("component_id"))
                link_type = l.find(".//{%s}link_type" % (self.none))
                if link_type is not None:
                    of_.set_link_type(link_type.attrib.get("name"))
                cmgr = l.find(".//{%s}component_manager" % (self.none))
                if cmgr is not None:
                    of_.set_component_manager(cmgr.attrib.get("name"))

                for ref in l.iterchildren("{%s}interface_ref" % (self.none)):
                    of_.add_interface_id(ref.attrib.get("component_id"))
            else:
                self.raise_exception("Unknown link type!")

            links_.append(of_.serialize())
        return links_
