from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX
from rspecs.commons_of import DEFAULT_OPENFLOW
from rspecs.formatter_base import FormatterBase
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

    def add_datapath(self, rspec, dpath):
        d = etree.SubElement(rspec, "{%s}datapath" % (self.__of))
        d.attrib["component_id"] = dpath.get("component_id")
        d.attrib["component_manager_id"] = dpath.get("component_manager_id")
        d.attrib["dpid"] = dpath.get("dpid")

        for p in dpath.get('ports'):
            port = etree.SubElement(d, "{%s}port" % (self.__of))
            port.attrib["num"] = p.get("num")
            if p.get("name") is not None:
                port.attrib["name"] = p.get("name")

    def datapath(self, dpath):
        self.add_datapath(self.rspec, dpath)

    def add_of_link(self, rspec, link):
        l = etree.SubElement(rspec, "{%s}link" % (self.__of))
        l.attrib["component_id"] = link.get("component_id")

	dpids_ = link.get("dpids")
	ports_ = link.get("ports")
	for i in range(len(dpids_)):
	    dp = etree.SubElement(l, "{%s}datapath" % (self.__of))
	    dp.attrib["component_id"] = dpids_[i].get("component_id")
	    dp.attrib["component_manager_id"] = dpids_[i].get("component_manager_id")
	    dp.attrib["dpid"] = dpids_[i].get("dpid")

	    port = etree.SubElement(l, "{%s}port" % (self.__of))
	    port.attrib["port_num"] = ports_[i].get("port_num")

        #for d in link.get("dpids"):
        #    dp = etree.SubElement(l, "{%s}datapath" % (self.__of))
        #    dp.attrib["component_id"] = d.get("component_id")
        #    dp.attrib["component_manager_id"] = d.get("component_manager_id")
        #    dp.attrib["dpid"] = d.get("dpid")

        #for p in link.get("ports"):
        #    port = etree.SubElement(l, "{%s}port" % (self.__of))
        #    port.attrib["port_num"] = p.get("port_num")

    def of_link(self, link):
        self.add_of_link(self.rspec, link)

    def add_fed_link(self, rspec, link):
        l = etree.SubElement(rspec, "{%s}link" % (self.__of))
        l.attrib["component_id"] = link.get("component_id")

        ltype = etree.SubElement(l, "{%s}link_type" % (self.__of))
        ltype.attrib["name"] = link.get("link_type_name")

        cm = etree.SubElement(l, "{%s}component_manager" % (self.__of))
        cm.attrib["name"] = link.get("component_manager_name")

        for ifref in link.get("interface_ref_id"):
            ref = etree.SubElement(l, "{%s}interface_ref" % (self.__of))
            ref.attrib["component_id"] = ifref

    def fed_link(self, link):
        self.add_fed_link(self.rspec, link)
