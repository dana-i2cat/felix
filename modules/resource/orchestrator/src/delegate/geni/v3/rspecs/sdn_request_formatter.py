from lxml import etree
from delegate.geni.v3 import exceptions
from sdn_commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_OPENFLOW,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX

DEFAULT_REQ_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3/of-resv.xsd"


class OFv3RequestFormatter(object):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 openflow=DEFAULT_OPENFLOW,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        NSMAP = {None: "%s" % (xmlns),
                 "xs": "%s" % (xs),
                 "openflow": "%s" % (openflow)}
        self.__openflow = openflow
        self.__rspec = etree.Element("rspec", nsmap=NSMAP)
        self.__rspec.attrib["{%s}schemaLocation" % (xs)] = schema_location
        self.__rspec.attrib["type"] = "request"

    def sliver(self, description=None, ref=None, email=None):
        sliver_ = etree.SubElement(self.__rspec,
                                   "{%s}sliver" % (self.__openflow))
        if description:
            sliver_.attrib["description"] = description
        if ref:
            sliver_.attrib["ref"] = ref
        if email:
            sliver_.attrib["email"] = email

    def controller(self, url, type):
        s = self.__find_sliver()
        controller_ = etree.SubElement(s, "{%s}controller" % (self.__openflow))
        controller_.attrib["url"] = url
        controller_.attrib["type"] = type

    def group(self, name):
        s = self.__find_sliver()
        group_ = etree.SubElement(s, "{%s}group" % (self.__openflow))
        group_.attrib["name"] = name

    def datapath(self, group_name, dp):
        g = self.__find_group(group_name)
        self.__datapath(g, dp.component_id, dp.component_manager_id,
                        dp.dpid, dp.ports)

    def match(self, mtc):
        s = self.__find_sliver()
        match_ = etree.SubElement(s, "{%s}match" % (self.__openflow))

        for use_group in mtc.use_groups:
            use_group_ = etree.SubElement(match_,
                                          "{%s}use-group" % (self.__openflow))
            use_group_.attrib["name"] = use_group.get("name")

        for dp in mtc.datapaths:
            dp_ = dp.get("datapath")
            self.__datapath(match_, dp_.component_id, dp_.component_manager_id,
                            dp_.dpid, dp_.ports)

        if mtc.packet is not None:
            packet_ = etree.SubElement(match_,
                                       "{%s}packet" % (self.__openflow))
            self.__packet_sub_elem(packet_, mtc.packet, 'dl_src')
            self.__packet_sub_elem(packet_, mtc.packet, 'dl_dst')
            self.__packet_sub_elem(packet_, mtc.packet, 'dl_type')
            self.__packet_sub_elem(packet_, mtc.packet, 'dl_vlan')
            self.__packet_sub_elem(packet_, mtc.packet, 'nw_src')
            self.__packet_sub_elem(packet_, mtc.packet, 'nw_dst')
            self.__packet_sub_elem(packet_, mtc.packet, 'nw_proto')
            self.__packet_sub_elem(packet_, mtc.packet, 'tp_src')
            self.__packet_sub_elem(packet_, mtc.packet, 'tp_dst')

    def __find_sliver(self):
        sliver = self.__rspec.find("{%s}sliver" % (self.__openflow))
        if sliver is None:
            raise exceptions.RSpecError("Sliver tag not found!")
        return sliver

    def __find_group(self, name):
        # using xpath recursive
        groups = self.__rspec.findall(".//{%s}group" % (self.__openflow))
        for group in groups:
            if group.get("name") == name:
                return group
        raise exceptions.RSpecError("Group %s not found!" % (name))

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

    def __packet_sub_elem(self, element, data, tag):
        if data.get(tag) is not None:
            value_ = etree.SubElement(element,
                                      "{%s}%s" % (self.__openflow, tag))
            value_.attrib["value"] = data.get(tag)

    def __repr__(self):
        return etree.tostring(self.__rspec, pretty_print=True)
