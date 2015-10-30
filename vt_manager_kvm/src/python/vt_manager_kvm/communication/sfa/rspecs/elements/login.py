from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element

class Login(Element):
    fields = [
        'authentication',
        'hostname',
        'port',
        'username'
    ]
