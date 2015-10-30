from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element

class Execute(Element):
    fields = [
        'shell',
        'command',
    ]
