from delegate.geni.v3.rspecs.parser_base import ParserBase


class SERMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3AdvertisementParser, self).__init__(from_file, from_string)
