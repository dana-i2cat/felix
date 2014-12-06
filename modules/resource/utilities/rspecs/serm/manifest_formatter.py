from rspecs.tnrm.manifest_formatter import TNRMv3ManifestFormatter
from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DSL_PREFIX
from rspecs.commons_tn import DEFAULT_SHARED_VLAN
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DSL_PREFIX + "3/manifest.xsd "
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX +\
    "ext/shared-vlan/1/request.xsd"


class SERMv3ManifestFormatter(TNRMv3ManifestFormatter):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        super(SERMv3ManifestFormatter, self).__init__(
            xmlns, xs, sharedvlan, schema_location)

    def add_link(self, rspec, l):
        link_ = etree.SubElement(rspec, "{%s}link" % (self.xmlns))
        link_.attrib["client_id"] = l.get("component_id")

        if l.get("sliver_id") is not None:
            link_.attrib["sliver_id"] = l.get("sliver_id")

        if l.get("vlantag") is not None:
            link_.attrib["vlantag"] = l.get("vlantag")

        mgr_ = etree.SubElement(link_, "{%s}component_manager" % (self.xmlns))
        mgr_.attrib["name"] = l.get("component_manager_name")

        typee_ = etree.SubElement(link_, "{%s}link_type" % (self.xmlns))
        typee_.attrib["name"] = l.get("link_type")

        for i in l.get("interface_ref"):
            ifr_ = etree.SubElement(link_, "{%s}interface_ref" % (self.xmlns))
            ifr_.attrib["client_id"] = i.get("component_id")

        for p in l.get("property"):
            prop_ = etree.SubElement(link_, "{%s}property" % (self.xmlns))
            prop_.attrib["source_id"] = p.get("source_id")
            prop_.attrib["dest_id"] = p.get("dest_id")
            prop_.attrib["capacity"] = p.get("capacity")

    def link(self, l):
        self.add_link(self.rspec, l)
