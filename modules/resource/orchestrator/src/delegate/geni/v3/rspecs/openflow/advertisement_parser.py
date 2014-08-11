from commons import Node, OpenFlowNode
from commons import OpenFlowLink_dpid2dpid, OpenFlowLink_dpid2device
from delegate.geni.v3 import exceptions
from lxml import etree


class OFv3AdvertisementParser(object):
    def __init__(self, from_file=None, from_string=None):
        if from_file is not None:
            self.__rspec = etree.parse(from_file).getroot()
        elif from_string is not None:
            self.__rspec = etree.fromstring(from_string)

        self.__openflow = self.__rspec.nsmap.get('openflow')
        self.__none = self.__rspec.nsmap.get(None)

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

    def oflinks(self):
        oflinks_ = []
        for ofl in self.__rspec.findall(".//{%s}link" % (self.__openflow)):
            if ofl.attrib.get("dstDPID"):
                of_ = OpenFlowLink_dpid2dpid(ofl.attrib.get("srcDPID"),
                                             ofl.attrib.get("srcPort"),
                                             ofl.attrib.get("dstDPID"),
                                             ofl.attrib.get("dstPort"))
            elif ofl.attrib.get("dstDevice"):
                of_ = OpenFlowLink_dpid2device(ofl.attrib.get("srcDPID"),
                                               ofl.attrib.get("srcPort"),
                                               ofl.attrib.get("dstDevice"),
                                               ofl.attrib.get("dstPort"))
            oflinks_.append({'oflink': of_})
        return oflinks_

    def get_rspec(self):
        return self.__rspec

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
