from vt_manager_kvm.communication.sfa.rspecs.elements.element import Element  
from vt_manager_kvm.communication.sfa.rspecs.elements.execute import Execute  
from vt_manager_kvm.communication.sfa.rspecs.elements.install import Install  
from vt_manager_kvm.communication.sfa.rspecs.elements.services import Services  
from vt_manager_kvm.communication.sfa.rspecs.elements.login import Login

class PGv2Services:
    @staticmethod
    def add_services(xml, services):
        if not services:
            return 
        for service in services:
            service_elem = xml.add_element('services')
            child_elements = {'install': Install.fields,
                              'execute': Execute.fields,
                              'login': Login.fields}
            print child_elements.items()
            for (name, fields) in child_elements.items():
                child = service.get(name)
                if not child: 
                    continue
                if isinstance(child, dict):
                    service_elem.add_instance(name, child, fields)
                elif isinstance(child, list):
                    for obj in child:
                        service_elem.add_instance(name, obj, fields)
              
    @staticmethod
    def get_services(xml):
        services = []
        for services_elem in xml.xpath('./default:services | ./services'):
            service = Services(services_elem.attrib, services_elem)
            # get install 
            install_elems = xml.xpath('./default:install | ./install')
            service['install'] = [install_elem.get_instance(Install) for install_elem in install_elems]
            # get execute
            execute_elems = xml.xpath('./default:execute | ./execute')
            service['execute'] = [execute_elem.get_instance(Execute) for execute_elem in execute_elems]
            # get login
            login_elems = xml.xpath('./default:login | ./login')
            service['login'] = [login_elem.get_instance(Login) for login_elem in login_elems]
            services.append(service)  
        return services

