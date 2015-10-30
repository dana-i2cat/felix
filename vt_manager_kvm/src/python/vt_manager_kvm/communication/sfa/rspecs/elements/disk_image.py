from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element

class DiskImage(Element):
    fields = [
        'name',
        'os',
        'version',
        'description',
    ]        
