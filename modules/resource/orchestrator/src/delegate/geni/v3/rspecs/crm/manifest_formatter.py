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
    
    def add_sliver(self, rspec, n):
        sliver = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        # TODO sliver must include these fields before manifest!
        node_keys = ["geni_sliver_urn", "component_manager_id", "component_id", "sliver_id"]
        for key in node_keys:
            sliver.attrib[key] = getattr(n, key, "TODO: add field to sliver")
    
    def sliver(self, n):
        self.add_sliver(self.rspec, n)

    def generate(self, slivers):
        for s in slivers:
            self.sliver(s)
        return self.rspec

