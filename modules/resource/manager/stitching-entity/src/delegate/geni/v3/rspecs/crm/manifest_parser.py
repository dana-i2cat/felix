from delegate.geni.v3.rspecs.crm.request_parser import CRMv3RequestParser
from delegate.geni.v3.rspecs.commons_com import Sliver


class CRMv3ManifestParser(CRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3ManifestParser, self).__init__(from_file, from_string)

    def get_sliver(self, rspec=None):
        rspec = rspec or self.rspec
        sliver_list = []
        slivers = rspec.findall("{%s}node" % (self.xmlns))
        for sliver in slivers:
            sliver_info = {
                            "client_id": sliver.attrib.get("client_id"),
                            # Sliver's component manager is the CRM itself
                            "component_id": sliver.attrib.get("component_manager_id"),
                            "component_name": sliver.attrib.get("component_name"),
                            "sliver_id": sliver.attrib.get("sliver_id")
                            }
            sliver_list.append(sliver_info)
        return sliver_list

    def sliver(self):
        return self.get_sliver(self.rspec)
