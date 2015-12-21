from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX, PROTOGENI_PREFIX
from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.commons_tn import DEFAULT_SHARED_VLAN
from rspecs.formatter_base import FormatterBase
from rspecs.crm.advertisement_formatter import CRMv3AdvertisementFormatter
from rspecs.openflow.advertisement_formatter import OFv3AdvertisementFormatter
from rspecs.tnrm.advertisement_formatter import TNRMv3AdvertisementFormatter
from rspecs.serm.advertisement_formatter import SERMv3AdvertisementFormatter
from rspecs.vlink.advertisement_formatter import VLinkv3AdvertisementFormatter

from functools import wraps

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-ad.xsd"
DEFAULT_AD_SCHEMA_LOCATION += PROTOGENI_PREFIX
DEFAULT_AD_SCHEMA_LOCATION += PROTOGENI_PREFIX + "/ad.xsd"


class ROAdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 protogeni=PROTOGENI_PREFIX,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        # Every namespace is outputted, as the resulting RSpec
        # from RO is a mixture of them all
        ns_ = {"openflow": "%s" % (openflow),
               "sharedvlan": "%s" % (sharedvlan),
               "protogeni": "%s" % (protogeni)}
        super(ROAdvertisementFormatter, self).__init__(
            "advertisement", schema_location, ns_, xmlns, xs)
        self.__crm_formatter = CRMv3AdvertisementFormatter()
        self.__of_formatter = OFv3AdvertisementFormatter()
        self.__tnrm_formatter = TNRMv3AdvertisementFormatter()
        self.__serm_formatter = SERMv3AdvertisementFormatter()
        self.__vlink_formatter = VLinkv3AdvertisementFormatter()

    def check_inner_call_crm(func):
        @wraps(func)   
        def wrapper(*args, **kwargs):
            node = args[0]
            inner_call = True
            try:
                inner_call = args[1] or True
            except:
                pass
            if inner_call:
                node["component_manager_uuid"] = "felix:CRM"
            return func(*args, **kwargs)
        return wrapper

    def check_inner_call_serm(func):
        @wraps(func)   
        def wrapper(*args, **kwargs):
            node = args[0]
            inner_call = True
            try:
                inner_call = args[1] or True
            except:
                pass
            if inner_call:
                node["component_manager_uuid"] = "felix:SERM"
            return func(*args, **kwargs)
        return wrapper

    def check_inner_call_tnrm(func):
        @wraps(func)   
        def wrapper(*args, **kwargs):
            node = args[0]
            inner_call = True
            try:
                inner_call = args[1] or True
            except:
                pass
            if inner_call:
                node["component_manager_uuid"] = "felix:TNRM"
            return func(*args, **kwargs)
        return wrapper

    def check_inner_call_vlink(func):
        @wraps(func)   
        def wrapper(*args, **kwargs):
            node = args[0]
            inner_call = True
            try:
                inner_call = args[1] or True
            except:
                pass
            if inner_call:
                node["component_manager_uuid"] = "felix:VLink"
            return func(*args, **kwargs)
        return wrapper

    # COM resources
    def com_node(self, node, inner_call=False):
        self.__crm_formatter.add_node(self.rspec, node)

    def com_link(self, link, inner_call=False):
        self.__crm_formatter.add_link(self.rspec, link)

    # OF resources
    def datapath(self, dpath, inner_call=False):
        self.__of_formatter.add_datapath(self.rspec, dpath)

    def of_link(self, link, inner_call=False):
        self.__of_formatter.add_of_link(self.rspec, link)

    def fed_link(self, link, inner_call=False):
        self.__of_formatter.add_fed_link(self.rspec, link)

    # TN resources
    def tn_node(self, node, inner_call=False):
        self.__tnrm_formatter.add_node(self.rspec, node)

    def tn_link(self, link, inner_call=False):
        self.__tnrm_formatter.add_link(self.rspec, link)

    # SE resources
    def se_node(self, node, inner_call=False):
        self.__serm_formatter.add_node(self.rspec, node)

    def se_link(self, link, inner_call=False):
        self.__serm_formatter.add_link(self.rspec, link)

    # VL links
    def vl_link(self, link, inner_call=False):
        self.__vlink_formatter.add_link(self.rspec, link)
