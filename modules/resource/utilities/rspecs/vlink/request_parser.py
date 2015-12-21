from rspecs.parser_base import ParserBase
from rspecs.commons_se import SELink

import core
logger = core.log.getLogger("utility-rspec")


class VLinkv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(VLinkv3RequestParser, self).__init__(from_file, from_string)

    def check_vlink_resource(self, link, c_manager):
        # According to the proposed URNs structure, a virtual
        # link MUST have "mapper" as resource-name (client_id) 
        # and link type
        if "mapper" in c_manager.attrib.get("name") or "mapper" in link.attrib.get("client_id"):
            return True
        return False

    def get_links(self, rspec):
        links_ = []
        for l in rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in virtual link!")

            if not self.check_vlink_resource(l, manager_):
                logger.info("Skipping this link, not a virtual link: %s", (l,))
                continue

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
                        manager_.attrib.get("name"))

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_

    def links(self):
        return self.get_links(self.rspec)
