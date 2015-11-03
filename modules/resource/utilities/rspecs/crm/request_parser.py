from rspecs.commons import DEFAULT_XMLNS
from rspecs.commons_com import EMULAB_XMLNS, Sliver
from rspecs.parser_base import ParserBase

import core
logger = core.log.getLogger("utility-rspec")


class CRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3RequestParser, self).__init__(from_file, from_string)
        self.xmlns = DEFAULT_XMLNS
        self.__com = EMULAB_XMLNS

    def check_c_resource(self, node):
        # according to the proposed URNs structure, a C-node MUST have
        # "vtam" as resource-name (component_id) and authority
        # (component_manager_id) fields
        if (not node.attrib.get("component_id")) or\
           (not node.attrib.get("component_manager_id")):
            return False

        if ("vtam" in node.attrib.get("component_id")) and\
           ("vtam" in node.attrib.get("component_manager_id")):
            return True
        return False

    def get_slivers(self):
        # nodes = self.rspec.xpath("//d:node[@component_id='%s']" %\
        #               component_id, namespaces = {"d": self.xmlns})
        nodes = self.__find_nodes()
        sliver_list = []
        for node in nodes:
            if not self.check_c_resource(node):
                logger.info("Skipping this node, not a C-res: %s", (node,))
                continue

            logger.debug("Analizing C-res: %s" % (node,))

            server_c_id = node.attrib.get("component_id")
            server_cm_id = node.attrib.get("component_manager_id")
            server_client_id = node.attrib.get("client_id")
            server_exclusive = node.attrib.get("exclusive")
            server_available = False  # Default, not important at this point

            sliver_type = self.__find_sliver(node)
            sliver_type_name = sliver_type.attrib.get("name")
            ram = None
            disk = None
            cores = None
            img_instance = sliver_type.find(
                "{%s}xen" % self.rspec.nsmap.get("emulab"))  # EMULAB_XMLNS
            if img_instance is not None:
                cores = img_instance.attrib.get("cores")
                ram = img_instance.attrib.get("ram")
                disk = img_instance.attrib.get("disk")
            disk_image_name = "default"
            disk_image = sliver_type.find("{%s}disk_image" % self.xmlns)
            if disk_image is not None:
                disk_image_name = disk_image.attrib.get("name")
            sliver_elem = Sliver(server_c_id, server_cm_id, server_client_id,
                                 server_exclusive, server_available,
                                 sliver_type_name, disk_image_name,
                                 ram, disk, cores,
                                 )
            if sliver_elem is not None:
                # Retrieve contects of Sliver object
                sliver_list.append(sliver_elem.__dict__)
        return sliver_list

    def __find_sliver(self, node):
        sliver_type = node.find("{%s}sliver_type" % self.xmlns)
        if sliver_type is None:
            self.raise_exception("Sliver_type tag not found!")
        return sliver_type

    def __find_nodes(self):
        nodes = self.rspec.findall("{%s}node" % self.xmlns)
        if nodes is None:
            self.raise_exception("Node tag not found!")
        return nodes

    def get_nodes(self):
        return self.__find_nodes()

#    def __find_slivers(self, nodes=None):
#        slivers = []
#        if nodes is not None:
#            for node in nodes:
#                slivers.extend(node.findall("{%s}sliver_type" % self.xmlns))
#        else:
#            slivers = self.rspec.findall("{%s}sliver_type" % self.xmlns)
#        if slivers is None:
#            self.raise_exception("Sliver_type tag not found!")
#        return slivers
