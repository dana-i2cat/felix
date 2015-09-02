from extensions.sfa.util import xrn
from rspecs.parser_base import ParserBase
from rspecs.commons_com import Node, Link
from rspecs.commons import DEFAULT_XMLNS


class CRMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3AdvertisementParser, self).__init__(from_file, from_string)
        self.xmlns = DEFAULT_XMLNS
        self.__proto = self.rspec.nsmap.get('protogeni')

    def __update_protogeni_cm_uuid(self, tag, obj):
        cmuuid = tag.attrib.get("{%s}component_manager_uuid" % (self.__proto))
        if cmuuid is not None:
            obj.add_component_manager_uuid(cmuuid)

    def nodes(self):
        nodes = []

        # Retrieve interfaces from links and postprocess
        # the data before returning the links
        links = self.links()

        for n in self.rspec.iterchildren("{%s}node" % (self.xmlns)):
            # sliver = None
            available = n.find("{%s}available" % (self.xmlns))
            if available is not None:
                available = available.attrib.get("now")
            node = Node(n.attrib.get("component_id"),
                        n.attrib.get("component_manager_id"),
                        n.attrib.get("component_name"),
                        n.attrib.get("exclusive"), available)

            self.__update_protogeni_cm_uuid(n, node)

            # node_id = xrn.urn_to_hrn(n.get("component_id"))[0]
            for link in links:
                if len(link["links"]) <= 0:
                    continue
                # Retrieve source_id of link to find the
                # interfaces of the current node
                node_interface = xrn.urn_to_hrn(link["links"][0]["source_id"])
                # Otherwise, retrieve dest_id of link to find the interfaces
                # of the current node
                node_interface = node_interface or\
                    xrn.urn_to_hrn(link["links"][0]["dest_id"])

                if node_interface:
                    # Get last part of the interface resource
                    node_interface =\
                        xrn.urn_to_hrn(node_interface[0])[0].split(".")[-1]
                    node.add_interface(node_interface)

            nodes.append(node.serialize())
        return nodes

    def links(self):

        links = []

        for l in self.rspec.iterchildren("{%s}link" % self.xmlns):
            # Create link object
            link = Link(l.attrib.get("component_id"),
                        l.attrib.get("component_name"))

            link_type = l.find("{%s}link_type" % (self.xmlns))
            if link_type is not None:
                link_type = link_type.attrib.get("name")
                link.add_type(link_type)

            self.__update_protogeni_cm_uuid(l, link)

            # Fill with properties
            for p in l.iterchildren("{%s}property" % self.xmlns):
                link.add_link(p.attrib.get("source_id"),
                              p.attrib.get("dest_id"),
                              p.attrib.get("capacity"))

            links.append(link.serialize())

        return links
