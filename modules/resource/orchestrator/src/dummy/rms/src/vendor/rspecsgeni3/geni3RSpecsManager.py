import os
import sys

# Add RO source root to syspath (relative to main.py)
RO_SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../../../../utilities/"))
sys.path.append(RO_SRC) # src folder

from amsoil.core import serviceinterface
from rspecs.commons_com import Node as COMNode, Link as COMLink
from rspecs.crm.advertisement_formatter import CRMv3AdvertisementFormatter
from rspecs.crm.manifest_formatter import CRMv3ManifestFormatter
from rspecs.crm.request_parser import CRMv3RequestParser
from rspecs.openflow.advertisement_formatter import OFv3AdvertisementFormatter
from rspecs.commons_of import Datapath, Link as OFLink
from rspecs.commons import FEDLink, validate
from rspecs.openflow.request_parser import OFv3RequestParser
from rspecs.commons_tn import Node as TNNode, Interface, Link as TNLink
from rspecs.commons_se import SELink
from rspecs.serm.advertisement_formatter import SERMv3AdvertisementFormatter
from rspecs.serm.request_parser import SERMv3RequestParser
from rspecs.serm.manifest_formatter import SERMv3ManifestFormatter
from rspecs.tnrm.advertisement_formatter import TNRMv3AdvertisementFormatter
from rspecs.tnrm.manifest_formatter import TNRMv3ManifestFormatter
from rspecs.tnrm.request_parser import TNRMv3RequestParser


class Geni3RSpecsManager(object):

    @staticmethod
    @serviceinterface
    def get_COMLink(component_id, component_name, link_type=""):
        return COMLink(component_id, component_name, link_type)

    @staticmethod
    @serviceinterface
    def get_COMNode(ci, cmid, auth_cm, exclusive=False, available=True):
        return COMNode(ci, cmid, auth_cm, exclusive, available)

    @staticmethod
    @serviceinterface
    def get_CRMv3AdvertisementFormatter():
        return CRMv3AdvertisementFormatter()

    @staticmethod
    @serviceinterface
    def get_CRMv3RequestParser(from_file=None, from_string=None):
        return CRMv3RequestParser(from_file, from_string)

    @staticmethod
    @serviceinterface
    def get_CRMv3ManifestFormatter():
        return CRMv3ManifestFormatter()

    @staticmethod
    @serviceinterface
    def get_OFv3AdvertisementFormatter():
        return OFv3AdvertisementFormatter()

    @staticmethod
    @serviceinterface
    def get_Datapath(cid, cmid, dpid):
        return Datapath(cid, cmid, dpid)

    @staticmethod
    @serviceinterface
    def get_OFLink(cid):
        return OFLink(cid)

    @staticmethod
    @serviceinterface
    def get_FEDLink(cid):
        return FEDLink(cid)

    @staticmethod
    @serviceinterface
    def call_validate(rspec):
        return validate(rspec)

    @staticmethod
    @serviceinterface
    def get_OFv3RequestParser(from_file=None, from_string=None):
        return OFv3RequestParser(from_file, from_string)

    @staticmethod
    @serviceinterface
    def get_TNNode(cid, cmid, exclusive=None, sliver_type=None):
        return TNNode(cid, cmid, exclusive, sliver_type)

    @staticmethod
    @serviceinterface
    def get_Interface(cid):
        return Interface(cid)

    @staticmethod
    @serviceinterface
    def get_SELink(cid, typee, cmid=None, vlantag=None, sliver=None):
        return SELink(cid, typee, cmid, vlantag, sliver)

    @staticmethod
    @serviceinterface
    def get_SERMv3AdvertisementFormatter():
        return SERMv3AdvertisementFormatter()

    @staticmethod
    @serviceinterface
    def get_SERMv3RequestParser(from_file=None, from_string=None):
        return SERMv3RequestParser(from_file, from_string)

    @staticmethod
    @serviceinterface
    def get_SERMv3ManifestFormatter():
        return SERMv3ManifestFormatter()

    @staticmethod
    @serviceinterface
    def get_TNRMv3AdvertisementFormatter():
        return TNRMv3AdvertisementFormatter()

    @staticmethod
    @serviceinterface
    def get_TNRMv3ManifestFormatter():
        return TNRMv3ManifestFormatter()

    @staticmethod
    @serviceinterface
    def get_TNLink(cid, cmid, vlantag=None):
        return TNLink(cid, cmid, vlantag)

    @staticmethod
    @serviceinterface
    def get_TNRMv3RequestParser(from_file=None, from_string=None):
        return TNRMv3RequestParser(from_file, from_string)
