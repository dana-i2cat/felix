from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_OPENFLOW, DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "


class ROManifestFormatter(object):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        NSMAP = {None: "%s" % (xmlns),
                 "xs": "%s" % (xs),
                 "openflow": "%s" % (openflow)}
        self.__of = openflow
        self.__rspec = etree.Element("{%s}rspec" % (xmlns), nsmap=NSMAP)
        self.__rspec.attrib["{%s}schemaLocation" % (xs)] = schema_location
        self.__rspec.attrib["type"] = "manifest"

    # OF resources
    def sliver(self, description=None, ref=None, email=None):
        s = etree.SubElement(self.__rspec, "{%s}sliver" % (self.__of))
        if description is not None:
            s.attrib["description"] = description
        if ref is not None:
            s.attrib["ref"] = ref
        if email is not None:
            s.attrib["email"] = email

    def get_rspec(self):
        return self.__rspec

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
