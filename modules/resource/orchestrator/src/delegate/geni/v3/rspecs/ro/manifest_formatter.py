from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_of import DEFAULT_OPENFLOW
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_TN
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "


class ROManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 tn=DEFAULT_TN,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        ns_ = {"openflow": "%s" % (openflow),
               "tn": "%s" % (tn)}
        super(ROManifestFormatter, self).__init__(
            "manifest", schema_location, ns_, xmlns, xs)
        self.__of = openflow
        self.__tn = tn

    # OF resources
    def of_sliver(self, description=None, ref=None, email=None):
        s = etree.SubElement(self.rspec, "{%s}sliver" % (self.__of))
        if description is not None:
            s.attrib["description"] = description
        if ref is not None:
            s.attrib["ref"] = ref
        if email is not None:
            s.attrib["email"] = email

    # TN resources
    def tn_sliver(self, description=None, ref=None, email=None):
        s = etree.SubElement(self.rspec, "{%s}sliver" % (self.__tn))
        if description is not None:
            s.attrib["description"] = description
        if ref is not None:
            s.attrib["ref"] = ref
        if email is not None:
            s.attrib["email"] = email
