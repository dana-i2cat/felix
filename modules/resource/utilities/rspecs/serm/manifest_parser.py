from rspecs.serm.request_parser import SERMv3RequestParser
from rspecs.commons_se import SELink, SENode
from rspecs.commons_tn import Interface

import core
logger = core.log.getLogger("utility-rspec")


class SERMv3ManifestParser(SERMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3ManifestParser, self).__init__(from_file, from_string)
        self.__sv = self.rspec.nsmap.get('sharedvlan')

    def nodes(self):
        nodes = []
        for n in self.rspec.findall(".//{%s}node" % (self.none)):
            if not self.check_se_node_resource(n):
                logger.info("Skipping this node, not a SE-res: %s", (n,))
                continue

            host_name = None
            host = n.find("{%s}host" % (self.none))
            # For SERM manifest the host tag SHOULD be specified
            if host:
                host_name = host.attrib.get('name')

            node = SENode(n.attrib.get("client_id"),
                          n.attrib.get("component_manager_id"),
                          n.attrib.get("exclusive"),
                          hostname=host_name)

            self.update_protogeni_cm_uuid(n, node)

            for i in n.iterfind("{%s}interface" % (self.none)):
                interface = Interface(i.attrib.get("client_id"))
                for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                    interface.add_vlan(sv.attrib.get("vlantag"),
                                       sv.attrib.get("name"))
                node.add_interface(interface.serialize())

            nodes.append(node.serialize())
        return nodes

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            if not self.check_se_link_resource(l, manager_):
                logger.info("Skipping this link, not a SE-res: %s", (l,))
                continue

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
                        manager_.attrib.get("name"), l.attrib.get("vlantag"),
                        l.attrib.get("sliver_id"))

            self.update_protogeni_cm_uuid(l, l_)

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_
