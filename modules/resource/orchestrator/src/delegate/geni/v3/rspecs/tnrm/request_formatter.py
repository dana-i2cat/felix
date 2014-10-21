from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_SHARED_VLAN
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_REQ_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "ext/shared-vlan/1/ad.xsd"


class TNRMv3RequestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        super(TNRMv3RequestFormatter, self).__init__(
            "request", schema_location, {"sharedvlan": "%s" % (sharedvlan)},
            xmlns, xs)
        self.__sv = sharedvlan

    def node(self, n):
        node_ = etree.SubElement(self.rspec, "{%s}node" % (self.xmlns))
        node_.attrib["client_id"] = n.get("component_id")
        node_.attrib["component_manager_id"] = n.get("component_manager_id")
        node_.attrib["exclusive"] = n.get("exclusive")

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

    def link(self, l):
        link_ = etree.SubElement(self.rspec, "{%s}link" % (self.xmlns))
        link_.attrib["client_id"] = l.get("component_id")

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
