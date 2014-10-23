from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_of import DEFAULT_OPENFLOW
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_SHARED_VLAN
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from delegate.geni.v3.rspecs.openflow.advertisement_formatter\
    import OFv3AdvertisementFormatter
from delegate.geni.v3.rspecs.tnrm.advertisement_formatter\
    import TNv3AdvertisementFormatter

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-ad.xsd"


class ROAdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        ns_ = {"openflow": "%s" % (openflow),
               "sharedvlan": "%s" % (sharedvlan)}
        super(ROAdvertisementFormatter, self).__init__(
            "advertisement", schema_location, ns_, xmlns, xs)
        self.__of_formatter = OFv3AdvertisementFormatter()
        self.__tnrm_formatter = TNv3AdvertisementFormatter()

    # OF resources
    def datapath(self, dpath):
        self.__of_formatter.add_datapath(self.rspec, dpath)

    def of_link(self, link):
        self.__of_formatter.add_of_link(self.rspec, link)

    def fed_link(self, link):
        self.__of_formatter.add_fed_link(self.rspec, link)

    # TN resources
    def tn_node(self, node):
        self.__tnrm_formatter.add_node(self.rspec, node)

    def tn_link(self, link):
        self.__tnrm_formatter.add_link(self.rspec, link)
