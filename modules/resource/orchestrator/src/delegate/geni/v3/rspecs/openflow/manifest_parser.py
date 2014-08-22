from delegate.geni.v3.rspecs.commons import DEFAULT_OPENFLOW
from lxml import etree


class OFv3ManifestParser(object):
    def __init__(self, from_file=None, from_string=None):
        if from_file is not None:
            self.__rspec = etree.parse(from_file).getroot()
        elif from_string is not None:
            self.__rspec = etree.fromstring(from_string)

        self.__of = self.__rspec.nsmap.get('openflow')
        if self.__of is None:
            self.__of = DEFAULT_OPENFLOW
        self.__none = self.__rspec.nsmap.get(None)

    def sliver(self):
        s = self.__rspec.find("{%s}sliver" % (self.__of))
        if s is None:
            return None
        return {"description": s.attrib.get("description"),
                "ref": s.attrib.get("ref"),
                "email": s.attrib.get("email")}

    def get_rspec(self):
        return self.__rspec

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
