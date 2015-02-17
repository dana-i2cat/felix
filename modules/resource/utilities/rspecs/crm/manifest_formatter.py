from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX
from rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_MANIFEST_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_MANIFEST_SCHEMA_LOCATION += DSL_PREFIX + "3/manifest.xsd"


class CRMv3ManifestFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 schema_location=DEFAULT_MANIFEST_SCHEMA_LOCATION):
        super(CRMv3ManifestFormatter, self).__init__(
            "manifest", schema_location, {},
            xmlns, xs)
        self.__com = DEFAULT_XMLNS

    def add_sliver(self, rspec, n):
        sliver = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        # TODO sliver must include these fields before manifest!
        node_keys = ["geni_sliver_urn", "component_manager_id",
                     "component_id", "sliver_id"]
        for key in node_keys:
            sliver.attrib[key] = getattr(n, key, "TODO: add field to sliver")

    def sliver(self, n):
        self.add_sliver(self.rspec, n)

    def generate(self, slivers):
        for s in slivers:
            self.sliver(s)
        return self.rspec

    def add_node(self, rspec, n):
        node_ = etree.SubElement(rspec, "{%s}node" % (self.xmlns))
        node_.attrib["client_id"] = n.get("client_id")
        node_.attrib["component_id"] = n.get("component_id")
        node_.attrib["component_manager_id"] = n.get("component_manager_id")
        node_.attrib["sliver_id"] = n.get("sliver_id")

        if n.get("sliver_type_name") is not None:
            sliver_ = etree.SubElement(node_, "{%s}sliver_type" % (self.xmlns))
            sliver_.attrib["name"] = n.get("sliver_type_name")

        for s in n.get("services"):
            services_ = etree.SubElement(node_, "{%s}services" % (self.xmlns))
            if s.get("login") is not None:
                log_ = etree.SubElement(services_, "{%s}login" % (self.xmlns))
                log_.attrib["authentication"] =\
                    s.get("login").get("authentication")
                log_.attrib["hostname"] = s.get("login").get("hostname")
                log_.attrib["port"] = s.get("login").get("port")
                log_.attrib["username"] = s.get("login").get("username")

                if s.get("login").get("password") is not None:
                    log_.attrib["password"] = s.get("login").get("password")

    def node(self, n):
        self.add_node(self.rspec, n)
