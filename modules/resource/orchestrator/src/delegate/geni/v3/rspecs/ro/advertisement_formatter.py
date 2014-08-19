from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_OPENFLOW, DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from lxml import etree

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-ad.xsd"


class ROAdvertisementFormatter(object):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        NSMAP = {None: "%s" % (xmlns),
                 "xs": "%s" % (xs),
                 "openflow": "%s" % (openflow)}
        self.__of = openflow
        self.__xmlns = xmlns
        self.__rspec = etree.Element("{%s}rspec" % (xmlns), nsmap=NSMAP)
        self.__rspec.attrib["{%s}schemaLocation" % (xs)] = schema_location
        self.__rspec.attrib["type"] = "advertisement"

    # OF resources
    def datapath(self, dpath):
        d_ = etree.SubElement(self.__rspec,
                              "{%s}datapath" % (self.__of))
        d_.attrib["component_id"] = dpath.get("component_id")
        d_.attrib["component_manager_id"] = dpath.get("component_manager_id")
        d_.attrib["dpid"] = dpath.get("dpid")

        for p in dpath.get('ports'):
            port = etree.SubElement(d_, "{%s}port" % (self.__of))
            port.attrib["num"] = p.get("num")
            if p.get("name") is not None:
                port.attrib["name"] = p.get("name")

    def of_link(self, link):
        l_ = etree.SubElement(self.__rspec, "{%s}link" % (self.__xmlns))
        l_.attrib["component_id"] = link.get("component_id")

        for d in link.get("dpids"):
            dpat = etree.SubElement(l_, "{%s}datapath" % (self.__of))
            dpat.attrib["component_id"] = d.get("component_id")
            dpat.attrib["component_manager_id"] = d.get("component_manager_id")
            dpat.attrib["dpid"] = d.get("dpid")

        for p in link.get("ports"):
            port = etree.SubElement(l_, "{%s}port" % (self.__of))
            port.attrib["port_num"] = p.get("port_num")

    def fed_link(self, link):
        l_ = etree.SubElement(self.__rspec, "{%s}link" % (self.__xmlns))
        l_.attrib["component_id"] = link.get("component_id")

        ltype = etree.SubElement(l_, "{%s}link_type" % (self.__xmlns))
        ltype.attrib["name"] = link.get("link_type_name")

        cm = etree.SubElement(l_, "{%s}component_manager" % (self.__xmlns))
        cm.attrib["name"] = link.get("component_manager_name")

        for ifref in link.get("interface_ref_id"):
            ref = etree.SubElement(l_, "{%s}interface_ref" % (self.__xmlns))
            ref.attrib["component_id"] = ifref

    def get_rspec(self):
        return self.__rspec

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
