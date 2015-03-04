from rspecs.parser_base import ParserBase
from rspecs.crm.manifest_parser import CRMv3ManifestParser
from rspecs.openflow.manifest_parser import OFv3ManifestParser
from rspecs.serm.manifest_parser import SERMv3ManifestParser
from rspecs.tnrm.manifest_parser import TNRMv3ManifestParser


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
        except:
            return []

    # SDN resources (slivers)
    def sdn_slivers(self):
        try:
            return self.__of_parser.slivers()
        except:
            return []

    # SE resources (nodes & links)
    def se_nodes(self):
        try:
            nodes = self.__se_parser.nodes()
            return [n for n in nodes
                    if n.get('component_manager_uuid') == "felix:SERM"]
        except:
            return []

    def se_links(self):
        try:
            links = self.__se_parser.links()
            return [l for l in links
                    if l.get('component_manager_uuid') == "felix:SERM"]
        except:
            return []

    # TN resources (nodes & links)
    def tn_nodes(self):
        try:
            nodes = self.__tn_parser.nodes()
            return [n for n in nodes
                    if n.get('component_manager_uuid') == "felix:TNRM"]
        except:
            return []

    def tn_links(self):
        try:
            links = self.__tn_parser.links()
            return [l for l in links
                    if l.get('component_manager_uuid') == "felix:TNRM"]
        except:
            return []
