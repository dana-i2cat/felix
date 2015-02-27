from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, PROTOGENI_PREFIX
from rspecs.formatter_base import FormatterBase
from lxml import etree


class CRMv3AdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 protogeni=PROTOGENI_PREFIX,
                 schema_location=DEFAULT_XMLNS + "/ad.xsd"):
        super(CRMv3AdvertisementFormatter, self).__init__(
            "advertisement", schema_location,
            {"protogeni": "%s" % (protogeni)}, xmlns, xs)
        self.__proto = protogeni

    def add_node(self, rspec, node):
        n = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        n.attrib["component_manager_id"] = node.get("component_manager_id")
        n.attrib["component_name"] = node.get("component_name")
        n.attrib["component_id"] = node.get("component_id")
        n.attrib["exclusive"] = node.get("exclusive")

        if node.get("component_manager_uuid") is not None:
            n.attrib["{%s}component_manager_uuid" % (self.__proto)] =\
                node.get("component_manager_uuid")

        if node.get("available"):
            available = etree.SubElement(n, "{%s}available" % (self.xmlns))
            available.attrib["now"] = node.get("available")

    def node(self, node):
        self.add_node(self.rspec, node)

    def add_link(self, rspec, link):
        l = etree.SubElement(rspec, "{%s}link" % (self.xmlns))
        l.attrib["component_id"] = link.get("component_id")
        l.attrib["component_name"] = link.get("component_name")

        if link.get("component_manager_uuid") is not None:
            l.attrib["{%s}component_manager_uuid" % (self.__proto)] =\
                link.get("component_manager_uuid")

        for p in link.get("links"):
            prop = etree.SubElement(l, "{%s}property" % (self.xmlns))
            prop.attrib["source_id"] = p.get("source_id")
            prop.attrib["dest_id"] = p.get("dest_id")
            prop.attrib["capacity"] = p.get("capacity")

        link_type = etree.SubElement(l, "{%s}link_type" % (self.xmlns))
        link_type.attrib["name"] = link.get("link_type")

    def link(self, link):
        self.add_link(self.rspec, link)
