from lxml import etree
from delegate.geni.v3 import exceptions
from sdn_commons import Node, OpenFlowNode


class OFv3AdvertisementParser(object):
    def __init__(self, ingress):
        self.__rspec = etree.parse(ingress)
        self.__openflow = self.__rspec.getroot().nsmap.get('openflow')
        self.__none = self.__rspec.getroot().nsmap.get(None)

    def nodes(self):
        nodes_ = []
        for node in self.__rspec.findall(".//{%s}node" % (self.__none)):
            hname = self.__node_attrib(node, "hardware_type", "name")
            anow = self.__node_attrib(node, "available", "now")

            n_ = Node(node.attrib.get("component_id"),
                      node.attrib.get("component_manager_id"),
                      node.attrib.get("component_name"),
                      node.attrib.get("exclusive"),
                      hname, anow)
            nodes_.append({'node': n_})
        return nodes_

    def ofnodes(self):
        ofnodes_ = []
        for ofn in self.__rspec.findall(".//{%s}datapath" % (self.__openflow)):
            node_ = self.__find_node(ofn.attrib.get("component_id"),
                                     ofn.attrib.get("component_manager_id"),
                                     ofn.attrib.get("dpid"))
            excl = node_.attrib.get("exclusive")
            anow = self.__node_attrib(node_, "available", "now")

            of_ = OpenFlowNode(ofn.attrib.get("component_id"),
                               ofn.attrib.get("component_manager_id"),
                               ofn.attrib.get("dpid"),
                               excl, anow)

            [of_.add_port(p.attrib.get("num"), p.attrib.get("name"))
             for p in ofn.findall(".//{%s}port" % (self.__openflow))]

            ofnodes_.append({'ofnode': of_})
        return ofnodes_

    def __node_attrib(self, element, tag, name):
        value = element.find(".//{%s}%s" % (self.__none, tag))
        if value is None:
            raise exceptions.RSpecError("%s is not found!", tag)
        return value.attrib.get(name)

    def __find_node(self, cid, cmid, dpid):
        for node in self.__rspec.findall(".//{%s}node" % (self.__none)):
            if node.attrib.get("component_id") == cid and\
               node.attrib.get("component_manager_id") == cmid and\
               node.attrib.get("component_name") == dpid:
                return node
        raise exceptions.RSpecError("Node with %s,%s,%s is not found!",
                                    (cid, cmid, dpid))

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
