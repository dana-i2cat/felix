from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS,\
    DEFAULT_SCHEMA_LOCATION, DSL_PREFIX
from delegate.geni.v3.rspecs.commons_tn import DEFAULT_SHARED_VLAN
from delegate.geni.v3.rspecs.commons_com import EMULAB_XMLNS
from delegate.geni.v3.rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_REQ_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "3/request.xsd "
DEFAULT_REQ_SCHEMA_LOCATION += DSL_PREFIX + "ext/shared-vlan/1/ad.xsd"


class CRMv3RequestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 emulab=EMULAB_XMLNS,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        super(CRMv3RequestFormatter, self).__init__(
            "request", schema_location,
            {"sharedvlan": "%s" % (sharedvlan),
             "emulab": "%s" % (emulab)},
            xmlns, xs)
        self.__sv = sharedvlan
        self.__emulab = emulab

    def node(self, n):
        node_ = etree.SubElement(self.rspec, "{%s}node" % (self.xmlns))
        node_.attrib["component_id"] = n.get("component_id")
        node_.attrib["component_manager_id"] = n.get("component_manager_id")
        node_.attrib["client_id"] = n.get("client_id")

        if n.get("exclusive") is not None:
            node_.attrib["exclusive"] = n.get("exclusive")

        if n.get("sliver_type") is not None:
            sliver_ = etree.SubElement(node_, "{%s}sliver_type" % (self.xmlns))
            sliver_.attrib["name"] = n.get("sliver_type")

            disk_ = etree.SubElement(sliver_, "{%s}disk_image" % (self.xmlns))
            disk_.attrib["name"] = n.get("disk_image")

            xen_ = etree.SubElement(sliver_, "{%s}xen" % (self.__emulab))
            xen_.attrib["cores"] = n.get("cores")
            xen_.attrib["ram"] = n.get("ram")
            xen_.attrib["disk"] = n.get("disk")

    def link(self, l):
        link_ = etree.SubElement(self.rspec, "{%s}link" % (self.xmlns))
        link_.attrib["client_id"] = l.get("component_id")

        mgr_ = etree.SubElement(link_, "{%s}component_manager" % (self.xmlns))
        mgr_.attrib["name"] = l.get("component_manager_name")

        for i in l.get("interface_ref"):
            ifr_ = etree.SubElement(link_, "{%s}interface_ref" % (self.xmlns))
            ifr_.attrib["client_id"] = i.get("component_id")

        for p in l.get("links"):
            prop_ = etree.SubElement(link_, "{%s}property" % (self.xmlns))
            prop_.attrib["source_id"] = p.get("source_id")
            prop_.attrib["dest_id"] = p.get("dest_id")
            prop_.attrib["capacity"] = p.get("capacity")
