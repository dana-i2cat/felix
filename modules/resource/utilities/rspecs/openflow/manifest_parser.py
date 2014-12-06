from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.parser_base import ParserBase


class OFv3ManifestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(OFv3ManifestParser, self).__init__(from_file, from_string)
        self.__of = self.rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW

    def sliver(self):
        s = self.rspec.find("{%s}sliver" % (self.__of))
        if s is None:
            return None
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}
