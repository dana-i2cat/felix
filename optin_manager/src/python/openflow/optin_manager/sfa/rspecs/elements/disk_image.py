from openflow.optin_manager.sfa.rspecs.elements.element import Element

class DiskImage(Element):
    fields = [
        'name',
        'os',
        'version',
        'description',
    ]        
