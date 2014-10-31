from delegate.geni.v3.rspecs.serm.request_parser import SERMv3RequestParser


class SERMv3ManifestParser(SERMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3ManifestParser, self).__init__(from_file, from_string)
