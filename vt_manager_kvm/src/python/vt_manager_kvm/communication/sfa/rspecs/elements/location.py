from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element

class Location(Element):
    
    fields = [
        'country',
        'longitude',
        'latitude',
    ]
