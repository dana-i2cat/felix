from delegate.geni.v3.rspecs.commons import DEFAULT_XMLNS
from delegate.geni.v3.rspecs.commons_com import EMULAB_XMLNS, Sliver
from delegate.geni.v3.rspecs.parser_base import ParserBase


class CRMv3RequestParser(ParserBase):
    def __init__(self, from_file=None, from_string=None):
        super(CRMv3RequestParser, self).__init__(from_file, from_string)
        self.xmlns = DEFAULT_XMLNS
        self.__com = EMULAB_XMLNS

    def get_slivers(self):
#        nodes = self.rspec.xpath("//d:node[@component_id='%s']" % component_id,
#                namespaces = {"d": self.xmlns})
        nodes = self.__find_nodes()
        sliver_list = []
        for node in nodes:
            server_component_id = node.attrib.get("component_id")
            sliver_type = self.__find_sliver(node)
            sliver_type_name = sliver_type.attrib.get("name")
            ram = None
            disk = None
            cores = None
            img_instance = sliver_type.find("{%s}xen" % self.rspec.nsmap.get("emulab")) #EMULAB_XMLNS
            if img_instance is not None:
                cores = img_instance.attrib.get("cores")
                ram = img_instance.attrib.get("ram")
                disk = img_instance.attrib.get("disk")
            disk_image_name = "default"
            disk_image = sliver_type.find("{%s}disk_image" % self.xmlns)
            if disk_image is not None:
                disk_image_name = disk_image.attrib.get("name")
            sliver_elem = Sliver(server_component_id, sliver_type_name, disk_image_name, 
                        ram, disk, cores)
            if sliver_elem is not None:
                # Retrieve contects of Sliver object
                sliver_list.append(sliver_elem.__dict__["sliver"])
        return sliver_list

    def __find_nodes(self):
        nodes = self.rspec.findall("{%s}node" % self.xmlns)
        if nodes is None:
            self.raise_exception("Node tag not found!")
        return nodes

    def __find_sliver(self, node):
        sliver_type = node.find("{%s}sliver_type" % self.xmlns)
        if sliver_type is None:
            self.raise_exception("Sliver_type tag not found!")
        return sliver_type

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

