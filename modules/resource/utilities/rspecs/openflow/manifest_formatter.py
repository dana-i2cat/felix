from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX
from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/manifest.xsd"


class OFv3ManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        super(OFv3ManifestFormatter, self).__init__(
            "manifest", schema_location, {"openflow": "%s" % (openflow)},
            xmlns, xs)
        self.__of = openflow

    def add_sliver(self, rspec, s):
        sliver_ = etree.SubElement(rspec, "{%s}sliver" % (self.__of))
        sliver_.attrib["description"] = s.get("description")
        sliver_.attrib["email"] = s.get("email")
        sliver_.attrib["status"] = s.get("status")
        sliver_.attrib["urn"] = s.get("urn")

    def sliver(self, s):
        self.add_sliver(self.rspec, s)
