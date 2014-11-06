from delegate.geni.v3.rspecs.tnrm.request_parser import CRMv3RequestParser
from delegate.geni.v3.rspecs.commons_com import Link


class CRMv3ManifestParser(CRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3ManifestParser, self).__init__(from_file, from_string)

    def get_links(self, rspec):
        links_ = []
        for l in rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            l_ = Link(l.attrib.get("client_id"), manager_.attrib.get("name"),
                      l.attrib.get("vlantag"))

            for i in l.iterfind("{%s}interface_ref" % (self.none)):
                l_.add_interface_ref(i.attrib.get("client_id"))

            for p in l.iterfind("{%s}property" % (self.none)):
                l_.add_property(p.attrib.get("source_id"),
                                p.attrib.get("dest_id"),
                                p.attrib.get("capacity"))

            links_.append(l_.serialize())

        return links_

    def links(self):
        return self.get_links(self.rspec)
