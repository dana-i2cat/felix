from rspecs.parser_base import ParserBase
from rspecs.crm.request_parser import CRMv3RequestParser
from rspecs.openflow.request_parser import OFv3RequestParser
from rspecs.tnrm.request_parser import TNRMv3RequestParser
from rspecs.serm.request_parser import SERMv3RequestParser
from rspecs.vlink.request_parser import VLinkv3RequestParser

import core
logger = core.log.getLogger("utility-rspec")


class RORequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(RORequestParser, self).__init__(from_file, from_string)
        self.__com_parser = CRMv3RequestParser(from_file, from_string)
        self.__of_parser = OFv3RequestParser(from_file, from_string)
        self.__tn_parser = TNRMv3RequestParser(from_file, from_string)
        self.__se_parser = SERMv3RequestParser(from_file, from_string)
        self.__vl_parser = VLinkv3RequestParser(from_file, from_string)

    # COM resources
    def com_nodes(self):
        try:
            return self.__com_parser.get_nodes()
        except Exception as e:
            # It could be possible that some requests do not contain C-nodes
            logger.warning("com_nodes exception: %s", e)
            return []

    def com_slivers(self):
        try:
            return self.__com_parser.get_slivers()
        except Exception as e:
            # It could be possible that some requests do not contain C-slivers
            logger.warning("com_slivers exception: %s", e)
            return []

    # OF resources
    def of_sliver(self):
        try:
            return self.__of_parser.get_sliver(self.rspec)
        except Exception as e:
            # It could be possible that some requests do not contain OF-sliver
            logger.warning("of_sliver exception: %s", e)
            return None

    def of_controllers(self):
        return self.__of_parser.get_controllers(self.rspec)

    def of_groups(self):
        return self.__of_parser.get_groups(self.rspec)

    def of_matches(self):
        return self.__of_parser.get_matches(self.rspec)

    def of_groups_matches(self):
        return self.__of_parser.get_groups_matches(self.rspec)

    # TN resources
    def tn_nodes(self):
        try:
            return self.__tn_parser.get_nodes(self.rspec)
        except Exception as e:
            # It could be possible that some requests do not contain TN-nodes
            logger.warning("tn_nodes exception: %s", e)
            return []

    def tn_links(self):
        try:
            return self.__tn_parser.get_links(self.rspec)
        except Exception as e:
            # It could be possible that some requests do not contain TN-links
            logger.warning("tn_links exception: %s", e)
            return []

    # SE resources
    def se_nodes(self):
        try:
            return self.__se_parser.get_nodes(self.rspec)
        except Exception as e:
            # By default, the requests do not contain SE-nodes
            logger.warning("se_nodes exception: %s", e)
            return []

    def se_links(self):
        try:
            return self.__se_parser.get_links(self.rspec)
        except Exception as e:
            # By default, the requests do not contain SE-links
            logger.warning("se_links exception: %s", e)
            return []

    # VL (virtual links)
    def vl_links(self):
        try:
            return self.__vl_parser.get_links(self.rspec)
        except Exception as e:
            # By default, the requests do not contain Virtual-links
            logger.warning("virt_links exception: %s", e)
            return []

    # Parsers
    def get_com_parser(self):
        return self.__com_parser

    def get_of_parser(self):
        return self.__of_parser

    def get_tn_parser(self):
        return self.__tn_parser

    def get_se_parser(self):
        return self.__se_parser

    def get_vl_parser(self):
        return self.__vl_parser