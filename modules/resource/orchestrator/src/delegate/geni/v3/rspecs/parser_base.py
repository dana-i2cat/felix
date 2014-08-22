from delegate.geni.v3 import exceptions
from lxml import etree


class ParserBase(object):
    def __init__(self, from_file=None, from_string=None):
        if from_file is not None:
            self.rspec = etree.parse(from_file).getroot()
        elif from_string is not None:
            self.rspec = etree.fromstring(from_string)

        self.none = self.rspec.nsmap.get(None)

    def get_rspec(self):
        return self.rspec

    def raise_exception(self, msg):
        raise exceptions.RSpecError("[RSpec-Parser] %s" % (msg,))

    def __repr__(self):
        return etree.tostring(self.rspec, pretty_print=True)
