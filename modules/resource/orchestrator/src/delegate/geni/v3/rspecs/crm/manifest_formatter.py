from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_SHARED_VLAN
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/manifest.xsd"


class CRMv3ManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        super(CRMv3ManifestFormatter, self).__init__(
            "manifest", schema_location, {},
            xmlns, xs)
        self.__com = DEFAULT_XMLNS

    def add_node(self, rspec, n):
        node = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        server_component_id = n.get("geni_sliver_urn")
        node.attrib["client_id"] = server_component_id.split("+")[-1]
        node.attrib["component_id"] = server_component_id
        node.attrib["component_manager_id"] = ""
        node.attrib["sliver_id"] = server_component_id

    def node(self, n):
        self.add_node(self.rspec, n)

