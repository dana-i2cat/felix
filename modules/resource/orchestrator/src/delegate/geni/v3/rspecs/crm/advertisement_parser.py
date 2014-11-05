from delegate.geni.v3.rspecs.parser_base import ParserBase
from delegate.geni.v3.rspecs.commons_com import Node, Link
from handler.geni.v3.extensions.sfa.util import xrn

class CRMv3AdvertisementParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3AdvertisementParser, self).__init__(from_file, from_string)
        self.__com = "" #self.rspec.nsmap.get("")
    
    def nodes(self):
        
        nodes = []
        
        # TODO Check that this is retrieving nodes (maybe the current self.__com is not good for this case)
        #self.none = "http://www.geni.net/resources/rspec/3"
        for n in self.rspec.iterchildren("{%s}node" % (self.__com)):
            sliver = None
            available = n.find("{%s}sliver_type" % (self.__com))
            if available:
                available = available.attrib.get("now")
            node = Node(n.attrib.get("component_id"),
                  n.attrib.get("component_name"),
                  n.attrib.get("component_manager_id"),
                  n.attrib.get("exclusive"), available)
            
            nodes.append(node.serialize())
            
            # Retrieve interfaces from links and postprocess the data before returning the links
            links = self.links()
            for node in nodes:
                node_id = xrn.urn_to_hrn(node.get("component_id"))
                # Retrieve source_id of link to find the interfaces of the current node
                node_interface = filter(lambda l: node_id in xrn.urn_to_hrn(l["source_id"]), link["property"])
                # Otherwise, retrieve dest_id of link to find the interfaces of the current node
                node_interface = node_interface or filter(lambda l: node_id in xrn.urn_to_hrn(l["dest_id"]), link["property"])
                node_interface = xrn.urn_to_hrn(node_interface[0])[-1] # XXX Parse interface to be only the last part
                node["interfaces"].append(node_interface)

        return nodes
    
    def links(self):
        
        links = []
        
        for l in self.rspec.iterchildren("{%s}link" % self.__com):
            link = Link(l.attrib.get("component_id"),
                l.attrib.get("component_name"))
    
            link_type = n.find("{%s}link_type" % (self.__com))
            if link_type:
                link_type = link_type.attrib.get("name")
    
            for p in l.iterchildren("{%s}property" % self.__com):
                link.add_property(p.attrib.get("source_id"),
                    p.attrib.get("dest_id"),
                    p.attrib.get("capacity"))
            
            links.append(link.serialize())
        
        return links
