from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX
from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.commons_tn import DEFAULT_SHARED_VLAN
from rspecs.formatter_base import FormatterBase
from rspecs.crm.manifest_formatter import CRMv3ManifestFormatter
from rspecs.tnrm.manifest_formatter import TNRMv3ManifestFormatter
from rspecs.serm.manifest_formatter import SERMv3ManifestFormatter
from rspecs.openflow.manifest_formatter import OFv3ManifestFormatter

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/manifest.xsd "


class ROManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        ns_ = {"openflow": "%s" % (openflow),
               "sharedvlan": "%s" % (sharedvlan)}
        super(ROManifestFormatter, self).__init__(
            "manifest", schema_location, ns_, xmlns, xs)
        self.__com_formatter = CRMv3ManifestFormatter()
        self.__tn_formatter = TNRMv3ManifestFormatter()
        self.__se_formatter = SERMv3ManifestFormatter()
        self.__of_formatter = OFv3ManifestFormatter()

    # COM resources
    def com_sliver(self, n):
        self.__com_formatter.add_sliver(self.rspec, n)

    def com_node(self, n):
        self.__com_formatter.add_node(self.rspec, n)

    # OF resources
    def of_sliver(self, s):
        self.__of_formatter.add_sliver(self.rspec, s)

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
