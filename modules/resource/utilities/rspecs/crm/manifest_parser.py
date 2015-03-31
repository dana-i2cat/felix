from rspecs.crm.request_parser import CRMv3RequestParser
from rspecs.commons_com import COMNode

import core
logger = core.log.getLogger("utility-rspec")


class CRMv3ManifestParser(CRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3ManifestParser, self).__init__(from_file, from_string)
        self.__proto = self.rspec.nsmap.get('protogeni')

    def get_sliver(self, rspec=None):
        if self.rspec is not None:
            rspec = self.rspec
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

    def __update_protogeni_cm_uuid(self, tag, obj):
        cmuuid = tag.attrib.get("{%s}component_manager_uuid" % (self.__proto))
        if cmuuid is not None:
            obj.add_component_manager_uuid(cmuuid)

    def get_nodes(self, rspec):
        nodes_ = []
        for n in rspec.findall(".//{%s}node" % (self.none)):
            if not self.check_c_resource(n):
                logger.info("Skipping this node, not a C-res: %s", (n,))
                continue

            comnode = COMNode(n.attrib.get("client_id"),
                              n.attrib.get("component_id"),
                              n.attrib.get("component_manager_id"),
                              n.attrib.get("sliver_id"))

            self.__update_protogeni_cm_uuid(n, comnode)

            stn = n.find("{%s}sliver_type" % (self.none))
            if stn is not None:
                comnode.sliver_type(stn.attrib.get("name"))

            for s in n.iterfind("{%s}services" % (self.none)):
                for login in s.iterfind("{%s}login" % (self.none)):
                    comnode.add_service(login.attrib.get("authentication"),
                                        login.attrib.get("hostname"),
                                        login.attrib.get("port"),
                                        login.attrib.get("username"),
                                        login.attrib.get("password"))

            nodes_.append(comnode.serialize())

        return nodes_

    def nodes(self):
        return self.get_nodes(self.rspec)
