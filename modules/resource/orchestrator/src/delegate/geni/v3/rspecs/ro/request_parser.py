from delegate.geni.v3.rspecs.parser_base import ParserBase
from delegate.geni.v3.rspecs.openflow.request_parser import OFv3RequestParser
from delegate.geni.v3.rspecs.tnrm.request_parser import TNRMv3RequestParser


class RORequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(RORequestParser, self).__init__(from_file, from_string)
        self.__of_parser = OFv3RequestParser(from_file, from_string)
        self.__tn_parser = TNRMv3RequestParser(from_file, from_string)

    # OF resources
    def of_sliver(self):
        try:
            return self.__of_parser.get_sliver(self.rspec)
        except Exception:
            return None

    def of_controllers(self):
        return self.__of_parser.get_controllers(self.rspec)

    def of_groups(self):
        return self.__of_parser.get_groups(self.rspec)

    def of_matches(self):
        return self.__of_parser.get_matches(self.rspec)

    # TN resources
    def tn_nodes(self):
        try:
            return self.__tn_parser.get_nodes(self.rspec)
        except Exception:
            return []

    def tn_links(self):
        try:
            return self.__tn_parser.get_links(self.rspec)
        except Exception:
            return []
