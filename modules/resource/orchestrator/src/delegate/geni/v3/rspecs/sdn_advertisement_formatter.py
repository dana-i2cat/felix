from lxml import etree
from sdn_commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_OPENFLOW,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-ad.xsd"


class OFv3AdvertisementFormatter(object):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        NSMAP = {None: "%s" % (xmlns),
                 "xs": "%s" % (xs),
                 "openflow": "%s" % (openflow)}
        self.__openflow = openflow
        self.__rspec = etree.Element("rspec", nsmap=NSMAP)
        self.__rspec.attrib["{%s}schemaLocation" % (xs)] = schema_location
        self.__rspec.attrib["type"] = "advertisement"

    def datapath(self, dpath):
        node_ = etree.SubElement(self.__rspec, "node")
        node_.attrib["component_id"] = dpath.component_id
        node_.attrib["component_manager_id"] = dpath.component_manager_id
        node_.attrib["component_name"] = dpath.component_name
        node_.attrib["exclusive"] = dpath.exclusive

        sub_node_ = etree.SubElement(node_, "hardware_type")
        sub_node_.attrib["name"] = dpath.hardware_type_name

        sub_node_ = etree.SubElement(node_, "available")
        sub_node_.attrib["now"] = dpath.available_now

        self.__datapath(self.__rspec, dpath.component_id,
                        dpath.component_manager_id, dpath.dpid, dpath.ports)

    def __datapath(self, element, component_id, component_manager_id,
                   dpid, ports):
        datapath_ = etree.SubElement(element,
                                     "{%s}datapath" % (self.__openflow))
        datapath_.attrib["component_id"] = component_id
        datapath_.attrib["component_manager_id"] = component_manager_id
        datapath_.attrib["dpid"] = dpid

        for p in ports:
            port_ = etree.SubElement(datapath_, "{%s}port" % (self.__openflow))
            port_.attrib["num"] = p.get("num")
            if p.get("name") is not None:
                port_.attrib["name"] = p.get("name")

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
