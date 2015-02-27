from rspecs.parser_base import ParserBase
from rspecs.crm.advertisement_parser import CRMv3AdvertisementParser
from rspecs.openflow.advertisement_parser import OFv3AdvertisementParser
from rspecs.serm.advertisement_parser import SERMv3AdvertisementParser
from rspecs.tnrm.advertisement_parser import TNRMv3AdvertisementParser


class ROv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(ROv3AdvertisementParser, self).__init__(from_file, from_string)
        self.__com_parser = CRMv3AdvertisementParser(from_file, from_string)
        self.__of_parser = OFv3AdvertisementParser(from_file, from_string)
        self.__se_parser = SERMv3AdvertisementParser(from_file, from_string)
        self.__tn_parser = TNRMv3AdvertisementParser(from_file, from_string)

    # COM resources (nodes & links)
    def com_nodes(self):
        try:
            return self.__com_parser.nodes()
        except:
            return []

    def com_links(self):
        try:
            return self.__com_parser.links()
        except:
            return []

    # SDN resources (datapaths & links)
    def sdn_nodes(self):
        try:
            return self.__of_parser.datapaths()
        except:
            return []

    def sdn_links(self):
        try:
            return self.__of_parser.links()
        except:
            return []

    # SE resources (nodes & links)
    def se_nodes(self):
        try:
            return self.__se_parser.nodes()
        except:
            return []

    def se_links(self):
        try:
            return self.__se_parser.links()
        except:
            return []

    # TN resources (nodes & links)
    def tn_nodes(self):
        try:
            return self.__tn_parser.nodes()
        except:
            return []

    def tn_links(self):
        try:
            return self.__tn_parser.links()
        except:
            return []
