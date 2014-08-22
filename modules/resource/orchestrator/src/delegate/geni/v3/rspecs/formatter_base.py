from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS, DEFAULT_XS
from delegate.geni.v3 import exceptions
from lxml import etree


class FormatterBase(object):
    def __init__(self, type_, schema_location, nsmap,
                 xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS):
        nsmap[None] = "%s" % (xmlns)
        nsmap["xs"] = "%s" % (xs)

        self.rspec = etree.Element("{%s}rspec" % (xmlns), nsmap=nsmap)
        self.rspec.attrib["{%s}schemaLocation" % (xs)] = schema_location
        self.rspec.attrib["type"] = type_
        self.xmlns = xmlns

    def get_rspec(self):
        return self.rspec

    def raise_exception(self, msg):
        raise exceptions.RSpecError("[RSpec-Formatter] %s" % (msg,))

    def __repr__(self):
        return etree.tostring(self.rspec, pretty_print=True)
