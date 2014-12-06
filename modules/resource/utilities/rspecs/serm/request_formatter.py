from rspecs.tnrm.request_formatter import DEFAULT_XS,\
    TNRMv3RequestFormatter, DEFAULT_XMLNS, DEFAULT_SHARED_VLAN,\
    DEFAULT_REQ_SCHEMA_LOCATION
from lxml import etree


class SERMv3RequestFormatter(TNRMv3RequestFormatter):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        super(SERMv3RequestFormatter, self).__init__(
            xmlns, xs, sharedvlan, schema_location)

    def link(self, link):
        l = etree.SubElement(self.rspec, "{%s}link" % (self.xmlns))
        l.attrib["client_id"] = link.get("component_id")

        if link.get("component_manager_name") is not None:
            m = etree.SubElement(l, "{%s}component_manager" % (self.xmlns))
            m.attrib["name"] = link.get("component_manager_name")

        t = etree.SubElement(l, "{%s}link_type" % (self.xmlns))
        t.attrib["name"] = link.get("link_type")

        for i in link.get("interface_ref"):
            interface = etree.SubElement(l, "{%s}interface_ref" % (self.xmlns))
            interface.attrib["component_id"] = i.get("component_id")

        for p in link.get("property"):
            prop = etree.SubElement(l, "{%s}property" % (self.xmlns))
            prop.attrib["source_id"] = p.get("source_id")
            prop.attrib["dest_id"] = p.get("dest_id")
            prop.attrib["capacity"] = p.get("capacity")
