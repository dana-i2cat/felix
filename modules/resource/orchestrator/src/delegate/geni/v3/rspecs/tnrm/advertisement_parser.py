from delegate.geni.v3.rspecs.parser_base import ParserBase


class TNRMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3AdvertisementParser, self).__init__(from_file, from_string)
