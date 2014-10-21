from delegate.geni.v3.rspecs.commons_tn import DEFAULT_TN
from delegate.geni.v3.rspecs.parser_base import ParserBase


class TNRMv3ManifestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3ManifestParser, self).__init__(from_file, from_string)
        self.__tn = self.rspec.nsmap.get('tn')
        if self.__tn is None:
            self.__tn = DEFAULT_TN

    def sliver(self):
        s = self.rspec.find("{%s}sliver" % (self.__tn))
        if s is None:
            return None
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}
