from delegate.geni.v3.rspecs.parser_base import ParserBase


class TNRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3RequestParser, self).__init__(from_file, from_string)
