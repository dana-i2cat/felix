from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_of import DEFAULT_OPENFLOW
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-ad.xsd"


class OFv3AdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        super(OFv3AdvertisementFormatter, self).__init__(
            "advertisement", schema_location, {"openflow": "%s" % (openflow)},
            xmlns, xs)
        self.__of = openflow

    def datapath(self, dpath):
        node = etree.SubElement(self.rspec, "{%s}node" % (self.xmlns))
        node.attrib["component_id"] = dpath.get('component_id')
        node.attrib["component_manager_id"] = dpath.get('component_manager_id')
        node.attrib["component_name"] = dpath.get('component_name')
        node.attrib["exclusive"] = dpath.get('exclusive')

        sub_node = etree.SubElement(node, "{%s}hardware_type" % (self.xmlns))
        sub_node.attrib["name"] = dpath.get('hardware_type_name')

        sub_node = etree.SubElement(node, "{%s}available" % (self.xmlns))
        sub_node.attrib["now"] = dpath.get('available_now')

        self.__datapath(self.rspec,
                        dpath.get('component_id'),
                        dpath.get('component_manager_id'),
                        dpath.get('dpid'),
                        dpath.get('ports'))

    def __datapath(self, element, component_id, component_manager_id,
                   dpid, ports):
        datapath = etree.SubElement(element, "{%s}datapath" % (self.__of))
        datapath.attrib["component_id"] = component_id
        datapath.attrib["component_manager_id"] = component_manager_id
        datapath.attrib["dpid"] = dpid

        for p in ports:
            port = etree.SubElement(datapath, "{%s}port" % (self.__of))
            port.attrib["num"] = p.get("num")
            if p.get("name") is not None:
                port.attrib["name"] = p.get("name")
