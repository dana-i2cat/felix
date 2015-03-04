from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX, PROTOGENI_PREFIX
from rspecs.formatter_base import FormatterBase
from rspecs.commons_tn import DEFAULT_SHARED_VLAN
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/manifest.xsd "
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX +\
    "ext/shared-vlan/1/request.xsd"
DEFAULT_MANIFEST_SCHEMA_LOCATION += PROTOGENI_PREFIX
DEFAULT_MANIFEST_SCHEMA_LOCATION += PROTOGENI_PREFIX + "/manifest.xsd "


class TNRMv3ManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 protogeni=PROTOGENI_PREFIX,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        ns_ = {"sharedvlan": "%s" % (sharedvlan),
               "protogeni": "%s" % (protogeni)}
        super(TNRMv3ManifestFormatter, self).__init__(
            "manifest", schema_location, ns_, xmlns, xs)
        self.__sv = sharedvlan
        self.__proto = protogeni

    def add_node(self, rspec, n):
        node_ = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        node_.attrib["client_id"] = n.get("component_id")
        node_.attrib["component_manager_id"] = n.get("component_manager_id")
        if n.get("exclusive") is not None:
            node_.attrib["exclusive"] = n.get("exclusive")

        if n.get("component_manager_uuid") is not None:
            node_.attrib["{%s}component_manager_uuid" % (self.__proto)] =\
                n.get("component_manager_uuid")

        if n.get("sliver_type_name") is not None:
            sliver_ = etree.SubElement(node_, "{%s}sliver_type" % (self.xmlns))
            sliver_.attrib["name"] = n.get("sliver_type_name")

        for i in n.get("interfaces"):
            intf_ = etree.SubElement(node_, "{%s}interface" % (self.xmlns))
            intf_.attrib["client_id"] = i.get("component_id")

            for v in i.get("vlan"):
                svlan_ = etree.SubElement(intf_,
                                          "{%s}link_shared_vlan" % (self.__sv))
                svlan_.attrib["vlantag"] = v.get("tag")
                if v.get("name") is not None:
                    svlan_.attrib["name"] = v.get("name")
                if v.get("description") is not None:
                    svlan_.attrib["description"] = v.get("description")

    def node(self, n):
        self.add_node(self.rspec, n)

    def add_link(self, rspec, l):
        link_ = etree.SubElement(rspec, "{%s}link" % (self.xmlns))
        link_.attrib["client_id"] = l.get("component_id")

        if l.get("vlantag") is not None:
            link_.attrib["vlantag"] = l.get("vlantag")

        if l.get("component_manager_uuid") is not None:
            link_.attrib["{%s}component_manager_uuid" % (self.__proto)] =\
                l.get("component_manager_uuid")

        mgr_ = etree.SubElement(link_, "{%s}component_manager" % (self.xmlns))
        mgr_.attrib["name"] = l.get("component_manager_name")

        for i in l.get("interface_ref"):
            ifr_ = etree.SubElement(link_, "{%s}interface_ref" % (self.xmlns))
            ifr_.attrib["client_id"] = i.get("component_id")

        for p in l.get("property"):
            prop_ = etree.SubElement(link_, "{%s}property" % (self.xmlns))
            prop_.attrib["source_id"] = p.get("source_id")
            prop_.attrib["dest_id"] = p.get("dest_id")
            prop_.attrib["capacity"] = p.get("capacity")

    def link(self, l):
        self.add_link(self.rspec, l)
