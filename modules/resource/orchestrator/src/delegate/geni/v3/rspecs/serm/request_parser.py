from delegate.geni.v3.rspecs.parser_base import ParserBase


class SERMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3RequestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')
