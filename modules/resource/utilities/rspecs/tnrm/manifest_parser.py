from rspecs.tnrm.request_parser import TNRMv3RequestParser
from rspecs.commons_tn import Node, Link, Interface


class TNRMv3ManifestParser(TNRMv3RequestParser):
    """
    Manifest parser inherits from request parser 
    as they use basically the same structure
    """
    def __init__(self, from_file=None, from_string=None):
        super(TNRMv3ManifestParser, self).__init__(from_file, from_string)

    def get_links(self, rspec):
        tn_links = []
        for l in rspec.findall(".//{%s}link" % (self.none)):
            manager = l.find("{%s}component_manager" % (self.none))
            if manager is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            tn_link = Link(l.attrib.get("client_id"), manager.attrib.get("name"),
                      l.attrib.get("vlantag"))

            for i in l.iterfind("{%s}interface_ref" % (self.none)):
                tn_link.add_interface_ref(i.attrib.get("client_id"))

            for p in l.iterfind("{%s}property" % (self.none)):
                tn_link.add_property(p.attrib.get("source_id"),
                                p.attrib.get("dest_id"),
                                p.attrib.get("capacity"))

            tn_links.append(tn_link.serialize())
        return tn_links

    def links(self):
        return self.get_links(self.rspec)
