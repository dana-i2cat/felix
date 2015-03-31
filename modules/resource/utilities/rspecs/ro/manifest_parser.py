from rspecs.parser_base import ParserBase
from rspecs.crm.manifest_parser import CRMv3ManifestParser
from rspecs.openflow.manifest_parser import OFv3ManifestParser
from rspecs.serm.manifest_parser import SERMv3ManifestParser
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser

import core
logger = core.log.getLogger("utility-rspec")


class ROManifestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(ROManifestParser, self).__init__(from_file, from_string)
        self.__com_parser = CRMv3ManifestParser(from_file, from_string)
        self.__of_parser = OFv3ManifestParser(from_file, from_string)
        self.__se_parser = SERMv3ManifestParser(from_file, from_string)
        self.__tn_parser = TNRMv3ManifestParser(from_file, from_string)

    # COM resources (nodes)
    def com_nodes(self):
        try:
            nodes = self.__com_parser.nodes()
            return [n for n in nodes
                    if n.get('component_manager_uuid') == "felix:CRM"]
        except Exception as e:
            logger.warning("com_nodes exception: %s", e)
            return []

    # SDN resources (slivers)
    def sdn_slivers(self):
        try:
            return self.__of_parser.slivers()
        except Exception as e:
            logger.warning("sdn_slivers exception: %s", e)
            return []

    # SE resources (nodes & links)
    def se_nodes(self):
        try:
            nodes = self.__se_parser.nodes()
            return [n for n in nodes
                    if n.get('component_manager_uuid') == "felix:SERM"]
        except Exception as e:
            logger.warning("se_nodes exception: %s", e)
            return []

    def se_links(self):
        try:
            links = self.__se_parser.links()
            return [l for l in links
                    if l.get('component_manager_uuid') == "felix:SERM"]
        except Exception as e:
            logger.warning("se_links exception: %s", e)
            return []

    # TN resources (nodes & links)
    def tn_nodes(self):
        try:
            nodes = self.__tn_parser.nodes()
            return [n for n in nodes
                    if n.get('component_manager_uuid') == "felix:TNRM"]
        except Exception as e:
            logger.warning("tn_nodes exception: %s", e)
            return []

    def tn_links(self):
        try:
            links = self.__tn_parser.links()
            return [l for l in links
                    if l.get('component_manager_uuid') == "felix:TNRM"]
        except Exception as e:
            logger.warning("tn_links exception: %s", e)
            return []
