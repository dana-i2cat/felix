from commons import Datapath, OFLink, FEDLink
from delegate.geni.v3 import exceptions
from lxml import etree


class OFv3AdvertisementParser(object):
    def __init__(self, from_file=None, from_string=None):
        if from_file is not None:
            self.__rspec = etree.parse(from_file).getroot()
        elif from_string is not None:
            self.__rspec = etree.fromstring(from_string)

        self.__of = self.__rspec.nsmap.get('openflow')
        self.__none = self.__rspec.nsmap.get(None)

    def ofdatapaths(self):
        ofdps_ = []
        for ofd in self.__rspec.iterchildren("{%s}datapath" % (self.__of)):
            of_ = Datapath(ofd.attrib.get("component_id"),
                           ofd.attrib.get("component_manager_id"),
                           ofd.attrib.get("dpid"))

            [of_.add_port(p.attrib.get("num"), p.attrib.get("name"))
             for p in ofd.findall(".//{%s}port" % (self.__of))]

            ofdps_.append(of_.serialize())
        return ofdps_

    def links(self):
        links_ = []
        for l in self.__rspec.findall(".//{%s}link" % (self.__none)):
            if l.find(".//{%s}datapath" % (self.__of)) is not None:
                of_ = OFLink(l.attrib.get("component_id"))
                for dpid in l.iterchildren("{%s}datapath" % (self.__of)):
                    d = Datapath(dpid.attrib.get("component_id"),
                                 dpid.attrib.get("component_manager_id"),
                                 dpid.attrib.get("dpid"))
                    of_.add_datapath(d)

                for port in l.iterchildren("{%s}port" % (self.__of)):
                    of_.add_port(port.attrib.get("port_num"))

            elif l.find(".//{%s}interface_ref" % (self.__none)) is not None:
                of_ = FEDLink(l.attrib.get("component_id"))
                link_type = l.find(".//{%s}link_type" % (self.__none))
                if link_type is not None:
                    of_.set_link_type(link_type.attrib.get("name"))
                cmgr = l.find(".//{%s}component_manager" % (self.__none))
                if cmgr is not None:
                    of_.set_component_manager(cmgr.attrib.get("name"))

                for ref in l.iterchildren("{%s}interface_ref" % (self.__none)):
                    of_.add_interface_id(ref.attrib.get("component_id"))
            else:
                raise exceptions.RSpecError("Unknown link type!")

            links_.append(of_.serialize())
        return links_

    def get_rspec(self):
        return self.__rspec

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
