from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from rspecs.commons_tn import DEFAULT_SHARED_VLAN
from rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/shared-vlan/1/ad.xsd"


class TNv3AdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        super(TNv3AdvertisementFormatter, self).__init__(
            "advertisement", schema_location,
            {"sharedvlan": "%s" % (sharedvlan)}, xmlns, xs)
        self.__sv = sharedvlan

    def node(self, node):
        n = etree.SubElement(self.rspec, "{%s}node" % (self.xmlns))
        n.attrib["component_id"] = node.get("component_id")
        n.attrib["component_manager_id"] = node.get("component_manager_id")
        n.attrib["exclusive"] = node.get("exclusive")

        if node.get("sliver_type_name") is not None:
            s = etree.SubElement(n, "{%s}sliver_type" % (self.xmlns))
            s.attrib["name"] = node.get("sliver_type_name")

        for i in node.get("interfaces"):
            interface = etree.SubElement(n, "{%s}interface" % (self.xmlns))
            interface.attrib["component_id"] = i.get("component_id")

            for v in i.get("vlan"):
                available = etree.SubElement(interface,
                                             "{%s}available" % (self.__sv))
                available.attrib["localTag"] = v.get("tag")
                if v.get("name") is not None:
                    available.attrib["name"] = v.get("name")
                if v.get("description") is not None:
                    available.attrib["description"] = v.get("description")

    def link(self, link):
        l = etree.SubElement(self.rspec, "{%s}link" % (self.xmlns))
        l.attrib["component_id"] = link.get("component_id")

        m = etree.SubElement(l, "{%s}component_manager" % (self.xmlns))
        m.attrib["name"] = link.get("component_manager_name")

        for i in link.get("interface_ref"):
            interface = etree.SubElement(l, "{%s}interface_ref" % (self.xmlns))
            interface.attrib["component_id"] = i.get("component_id")

        for p in link.get("property"):
            prop = etree.SubElement(l, "{%s}property" % (self.xmlns))
            prop.attrib["source_id"] = p.get("source_id")
            prop.attrib["dest_id"] = p.get("dest_id")
            prop.attrib["capacity"] = p.get("capacity")
