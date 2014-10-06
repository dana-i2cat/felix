from vt_manager.communication.sfa.rspecs.elements.element import Element
from vt_manager.communication.sfa.rspecs.elements.sliver import Sliver
from vt_manager.communication.sfa.rspecs.elements.versions.pgv2DiskImage import PGv2DiskImage
from vt_manager.communication.sfa.rspecs.elements.versions.plosv1FWRule import PLOSv1FWRule

class PGv2SliverType:

    @staticmethod
    def add_slivers(xml, slivers):
        if not slivers:
            return 
        if not isinstance(slivers, list):
            slivers = [slivers]
        for sliver in slivers: 
            sliver_elem = xml.add_element('sliver_type')
            if sliver.get('type'):
                sliver_elem.set('name', sliver['type'])
            attrs = ['client_id', 'cpus', 'memory', 'storage']
            for attr in attrs:
                if sliver.get(attr):
                    sliver_elem.set(attr, sliver[attr])
            
            images = sliver.get('disk_image')
            if images and isinstance(images, list):
                PGv2DiskImage.add_images(sliver_elem, images)      
            fw_rules = sliver.get('fw_rules')
            if fw_rules and isinstance(fw_rules, list):
                PLOSv1FWRule.add_rules(sliver_elem, fw_rules)
            PGv2SliverType.add_sliver_attributes(sliver_elem, sliver.get('tags', []))
    
    @staticmethod
    def add_sliver_attributes(xml, attributes):
        if attributes: 
            for attribute in attributes:
                if attribute['name'] == 'initscript':
                    xml.add_element('{%s}initscript' % xml.namespaces['planetlab'], name=attribute['value'])
                elif attribute['tagname'] == 'flack_info':
                    attrib_elem = xml.add_element('{%s}info' % self.namespaces['flack'])
                    attrib_dict = eval(tag['value'])
                    for (key, value) in attrib_dict.items():
                        attrib_elem.set(key, value)                
    @staticmethod
    def get_slivers(xml, filter={}):
        xpath = './default:sliver_type | ./sliver_type'
        sliver_elems = xml.xpath(xpath)
        slivers = []
        for sliver_elem in sliver_elems:
            sliver = Sliver(sliver_elem.attrib,sliver_elem)
            if 'component_id' in xml.attrib:     
                sliver['component_id'] = xml.attrib['component_id']
            if 'name' in sliver_elem.attrib:
                sliver['type'] = sliver_elem.attrib['name']
            sliver['disk_image'] = PGv2DiskImage.get_images(sliver_elem)
            sliver['fw_rules'] = PLOSv1FWRule.get_rules(sliver_elem)
            slivers.append(sliver)
        return slivers

    @staticmethod
    def get_sliver_attributes(xml, filter={}):
        return []             
