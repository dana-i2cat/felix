from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.commons_of import OFSliver
from rspecs.parser_base import ParserBase


class OFv3ManifestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(OFv3ManifestParser, self).__init__(from_file, from_string)
        self.__of = self.rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW

    def get_slivers(self, rspec):
        slivers_ = []
        for s in rspec.findall(".//{%s}sliver" % (self.__of)):
            ofsliver = OFSliver(s.attrib.get("description"),
                                s.attrib.get("email"),
                                s.attrib.get("status"),
                                s.attrib.get("urn"))

            slivers_.append(ofsliver.serialize())

        return slivers_

    def slivers(self):
        return self.get_slivers(self.rspec)
