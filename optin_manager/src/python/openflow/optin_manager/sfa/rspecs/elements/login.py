from openflow.optin_manager.sfa.rspecs.elements.element import Element

class Login(Element):
    fields = [
        'authentication',
        'hostname',
        'port',
        'username'
    ]
