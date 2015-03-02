from rspecs.tnrm.advertisement_formatter import DEFAULT_XS,\
    TNRMv3AdvertisementFormatter, DEFAULT_XMLNS, DEFAULT_SHARED_VLAN,\
    DEFAULT_AD_SCHEMA_LOCATION
from rspecs.commons import PROTOGENI_PREFIX
from lxml import etree


class SERMv3AdvertisementFormatter(TNRMv3AdvertisementFormatter):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 protogeni=PROTOGENI_PREFIX,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        super(SERMv3AdvertisementFormatter, self).__init__(
            xmlns, xs, sharedvlan, protogeni, schema_location)

    def add_link(self, rspec, link):
        l = etree.SubElement(rspec, "{%s}link" % (self.xmlns))
        l.attrib["component_id"] = link.get("component_id")

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

    def link(self, link):
        self.add_link(self.rspec, link)
