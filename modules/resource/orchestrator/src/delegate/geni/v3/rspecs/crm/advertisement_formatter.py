from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from lxml import etree

import core
logger = core.log.getLogger("com-advertisement-formatter")

class CRMv3AdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 schema_location=DEFAULT_XMLNS + "/ad.xsd"):
        super(CRMv3AdvertisementFormatter, self).__init__(
            "advertisement", schema_location,
            {}, xmlns, xs)

    def add_node(self, rspec, node):
        n = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        n.attrib["component_manager_id"] = node.get("component_manager_id")
        n.attrib["component_name"] = node.get("component_name")
        n.attrib["component_id"] = node.get("component_id")
        n.attrib["exclusive"] = node.get("exclusive")

        if node.get("available"):
            available = etree.SubElement(n, "{%s}available" % (self.xmlns))
            available.attrib["now"] = node.get("available")


    def node(self, node):
        self.add_node(self.rspec, node)

    def add_link(self, rspec, link):
        l = etree.SubElement(rspec, "{%s}link" % (self.xmlns))
        l.attrib["component_id"] = link.get("component_id")
        l.attrib["component_name"] = link.get("component_name")

        for p in link.get("property"):
            prop = etree.SubElement(l, "{%s}property" % (self.xmlns))
            prop.attrib["source_id"] = p.get("source_id")
            prop.attrib["dest_id"] = p.get("dest_id")
            prop.attrib["capacity"] = p.get("capacity")

    def link(self, link):
        self.add_link(self.rspec, link)
