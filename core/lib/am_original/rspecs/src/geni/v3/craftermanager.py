class CrafterManager:
    
    #TODO: Take into account extensions
    
    def __init__(self, resources=[], options={}):
        self.resources = resources
        self.options = options
        self._urn_authority = "urn:publicID:MYAUTHORITY"
        
    def get_advertisement(self, resources):
        output  = self.advert_header()
        for resource in resources:
            output += self.advert_resource(resource)
        output += self.advert_footer()
        return output    
    
    def advert_template(self):
        tmpl = '''<node component_manager_id="%s" component_name="%s" component_id="%s" exclusive="%s">
<available now="%s"/>
</node>
'''
        return tmpl
    
    def advert_resource(self, resource):
        resource_component_manager_id = str(resource.get_component_manager_id())
        resource_exclusive = str(resource.get_exclusive()).lower()
        resource_available = str(resource.get_available()).lower()
        resource_component_name = resource.get_component_name()
        resource_component_id = resource.get_component_id()
        return self.advert_template() % (resource_component_manager_id,
                       resource_component_name,
                       resource_component_id,
                       resource_exclusive,
                       resource_available)
    
    def advert_header(self):
        header = '''<?xml version="1.0" encoding="UTF-8"?>
<rspec xmlns="http://www.geni.net/resources/rspec/3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/ad.xsd" type="advertisement">\n'''
        return header
    
    def advert_footer(self):
        return '</rspec>\n'
    
    def manifest_header(self):
        header = '''<?xml version="1.0" encoding="UTF-8"?>
<rspec xmlns="http://www.geni.net/resources/rspec/3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/manifest.xsd" type="manifest">\n'''
        return header
    
    def manifest_template(self):
        template ='''<node client_id="%s" component_id="%s" component_manager_id="%s" sliver_id="%s">\n'''
        return template    
    
    def manfiest_node_close_tempalte(self):
        template ='''</node>\n'''
        return template
    
    def manifest_sliver_type_template(self):
        template = '''<sliver_type name="%s"/>\n'''
        return template
    
    def manifest_services_template(self):
        template = '''<services>\n<login authentication="ssh-keys" hostname="%s" port="22" username="%s"/>\n</services>\n'''
        return template
        
    def manifest_slivers(self, resources):
        result = ""
        for resource in resources:
            sliver = resource.get_sliver() 
            result += self.manifest_template() % (sliver.get_client_id(), resource.get_component_id(), resource.get_component_manager_id(), sliver.get_urn())
            if sliver.get_type():
                result += self.manifest_sliver_type_template() %(resource.get_id)
            if sliver.get_services():
                services = sliver.get_services()
                result += self.manifest_services_template() %(services["login"]["hostname"], services["login"]["username"])
            result += self.manfiest_node_close_tempalte()
        return result
    
    def manifest_footer(self):
        return '</rspec>\n'

