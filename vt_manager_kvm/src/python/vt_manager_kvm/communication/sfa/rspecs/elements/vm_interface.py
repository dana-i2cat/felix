from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element

class VMInterface(Element):
    fields = ['name',
              'mac',
              'ip',
              'mask',
              'gw',
              'dns1',
              'dns2',
    ]    
