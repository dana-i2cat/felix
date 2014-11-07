from delegate.geni.v3.rspecs.parser_base import ParserBase
from delegate.geni.v3.rspecs.commons_com import Node, Link
from handler.geni.v3.extensions.sfa.util import xrn
from delegate.geni.v3.rspecs.commons_com import DEFAULT_COM

import core
logger = core.log.getLogger("com-advertisement-parser")

class CRMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3AdvertisementParser, self).__init__(from_file, from_string)
        self.__com = DEFAULT_COM
    
    def nodes(self):
        from lxml import etree
        nodes = []

        # TODO Check that this is retrieving nodes (maybe the current self.__com is not good for this case)
        #self.none = "http://www.geni.net/resources/rspec/3"

        # Retrieve interfaces from links and postprocess the data before returning the links
        links = self.links()

        for n in self.rspec.iterchildren("{%s}node" % (self.__com)):
            sliver = None
            available = n.find("{%s}available" % (self.__com))
            if available is not None:
                available = available.attrib.get("now")
            node = Node(n.attrib.get("component_id"),
                  n.attrib.get("component_name"),
                  n.attrib.get("component_manager_id"),
                  n.attrib.get("exclusive"), available)

            node_id = xrn.urn_to_hrn(n.get("component_id"))[0]
            for link in links:
                # Retrieve source_id of link to find the interfaces of the current node
                node_interface = xrn.urn_to_hrn(link["property"][0]["source_id"])
                # Otherwise, retrieve dest_id of link to find the interfaces of the current node
                node_interface = node_interface or xrn.urn_to_hrn(link["property"][0]["dest_id"])
            
                if node_interface:
                    # Get last part of the interface resource
                    node_interface = xrn.urn_to_hrn(node_interface[0])[0].split(".")[-1]
                    node.add_interface(node_interface)
            nodes.append(node.serialize())
        return nodes
    
    def links(self):
        
        links = []
        
        for l in self.rspec.iterchildren("{%s}link" % self.__com):
            link = Link(l.attrib.get("component_id"),
                l.attrib.get("component_name"))
    
            link_type = l.find("{%s}link_type" % (self.__com))
            if len(link_type):
                link_type = link_type.attrib.get("name")
    
            for p in l.iterchildren("{%s}property" % self.__com):
                link.add_property(p.attrib.get("source_id"),
                    p.attrib.get("dest_id"),
                    p.attrib.get("capacity"))
            
            links.append(link.serialize())
        
        return links
