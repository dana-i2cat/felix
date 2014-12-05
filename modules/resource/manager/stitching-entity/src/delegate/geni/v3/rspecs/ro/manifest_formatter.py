from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_of import DEFAULT_OPENFLOW
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_SHARED_VLAN
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from delegate.geni.v3.rspecs.crm.manifest_formatter import\
    CRMv3ManifestFormatter
from delegate.geni.v3.rspecs.tnrm.manifest_formatter import\
    TNRMv3ManifestFormatter
from delegate.geni.v3.rspecs.serm.manifest_formatter import\
    SERMv3ManifestFormatter
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "


class ROManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        ns_ = {"openflow": "%s" % (openflow),
               "sharedvlan": "%s" % (sharedvlan)}
        super(ROManifestFormatter, self).__init__(
            "manifest", schema_location, ns_, xmlns, xs)
        #self.__of = openflow
        #self.__com_formatter = CRMv3ManifestFormatter()
        #self.__tn_formatter = TNRMv3ManifestFormatter()
        self.__se_formatter = SERMv3ManifestFormatter()

    # COM resources
    def com_sliver(self, n):
        self.__com_formatter.add_sliver(self.rspec, n)

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
    def tn_node(self, n):
        self.__tn_formatter.add_node(self.rspec, n)

    def tn_link(self, l):
        self.__tn_formatter.add_link(self.rspec, l)

    # SE resources
    def se_node(self, n):
        self.__se_formatter.add_node(self.rspec, n)

    def se_link(self, l):
        self.__se_formatter.add_link(self.rspec, l)
