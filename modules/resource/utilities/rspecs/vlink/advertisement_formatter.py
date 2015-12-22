from core.utils.urns import URNUtils
from rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS, DEFAULT_SCHEMA_LOCATION,\
    DSL_PREFIX, PROTOGENI_PREFIX
from rspecs.formatter_base import FormatterBase
from lxml import etree

DEFAULT_AD_SCHEMA_LOCATION = DEFAULT_SCHEMA_LOCATION
DEFAULT_AD_SCHEMA_LOCATION += DSL_PREFIX + "3/ad.xsd "


class VLinkv3AdvertisementFormatter(FormatterBase):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 protogeni=PROTOGENI_PREFIX,
                 schema_location=DEFAULT_AD_SCHEMA_LOCATION):
        ns_ = {"protogeni": "%s" % (protogeni)}
        super(VLinkv3AdvertisementFormatter, self).__init__(
            "advertisement", schema_location,
            ns_, xmlns, xs)
        self.__proto = protogeni

    def add_link(self, rspec, link, inner_call=True):
        """
        Translates incoming dictionary:

        {"src_name": "urn:publicid:IDN+fms:src_auth:mapper+domain+domain1",
         "dst_name": "urn:publicid:IDN+fms:src_auth:mapper+domain+domain2",
         "link_type": "(gre|nsi)")

        into the expected tree structure:

        <link component_id="urn:publicid:IDN+fms:src_auth:mapper+link+domain1_domain2">
          <component_manager name="urn:publicid:IDN+fms:src_auth:mapper+authority+cm"/>
          <link_type name="urn:felix+virtual_link+type+(gre|nsi)"/>
          <interface_ref component_id="urn:publicid:IDN+fms:src_auth:mapper+domain+domain1"/>
          <interface_ref component_id="urn:publicid:IDN+fms:src_auth:mapper+domain+domain2"/>
        </link>

        and embeds it into the advertisement RSpec
        """
        l = etree.SubElement(rspec, "{%s}link" % (self.xmlns))

        # Retrieve list of connected domains per link
        end_links = [link.get("src_name"), link.get("dst_name")]
        link_doms = map(lambda x: x.split("+")[-1], end_links)
        src_auth = URNUtils.get_felix_authority_from_urn(link.get("src_name"))
        component_id = "urn:publicid:IDN+fms:%s:mapper+link+%s_%s" % (src_auth, link_doms[0], link_doms[1])
        l.attrib["component_id"] = component_id

        if inner_call and link.get("component_manager_uuid") is not None:
            l.attrib["{%s}component_manager_uuid" % (self.__proto)] =\
                link.get("component_manager_uuid")

        m = etree.SubElement(l, "{%s}component_manager" % (self.xmlns))
        m.attrib["name"] = "urn:publicid:IDN+fms:%s:mapper+authority+cm" % src_auth

        t = etree.SubElement(l, "{%s}link_type" % (self.xmlns))
        t.attrib["name"] = "urn:felix+virtual_link+type+%s" % link.get("link_type")

        for i in end_links:
            interface = etree.SubElement(l, "{%s}interface_ref" % (self.xmlns))
            interface.attrib["component_id"] = i

    def link(self, link, inner_call=True):
        self.add_link(self.rspec, link, inner_call)
