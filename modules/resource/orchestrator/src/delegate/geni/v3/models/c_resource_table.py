import pymongo
import core
logger = core.log.getLogger("c-model")


class Services(object):
    def __init__(self):
        self.__services = []
    
    def get(self):
        return self.__services
    
    def add(self, service_type, type_, name, start_value, end_value):
        service = {'service_type': service_type,
                   'type': type_,
                   'name': name,
                   'start_value': start_value,
                   'end_value': end_value}
        self.__services.append(service)

class CResourceTable(object):
    def __init__(self):
        self.table = pymongo.MongoClient().felix_ro.CResourceTable
        self.info = {'rm_uuid': None,
                     'network_name': None,
                     'node': {},
                     'hostname': None,
                     'name': None,
                     'operating_system': {},
                     'virtualization': None,
                     'cpu': {},
                     'memory': None,
                     'hdd_space_GB': None,
                     'agent_url': None,
                     'location': {},
                     'services': []}
    
    def __str__(self):
        return str(self.info)
    
    def network_name(self, name):
        self.info['network_name'] = name
    
    def node(self, c_id, cm_id, c_name, exclusive):
        self.info['node']['component_id'] = c_id
        self.info['node']['component_manager_id'] = cm_id
        self.info['node']['component_name'] = c_name
        self.info['node']['exclusive'] = exclusive
    
    def hostname(self, hname):
        self.info['hostname'] = hname
    
    def name(self, name):
        self.info['name'] = name
    
    def clear_services(self):
        del self.info['services'][:]
    
    def add_range_service(self, type_, name, start, end):
        self.info['services'].append({'service_type': "Range",
                                      'type': type_,
                                      'name': name,
                                      'start_value': start,
                                      'end_value': end})
    
    def add_netif_service(self, from_name, to_id, to_port):
        self.info['services'].append({'service_type': "NetworkInterface",
                                      'from_server_interface_name': from_name,
                                      'to_network_interface_id': to_id,
                                      'to_network_interface_port': to_port})
    
    def is_range_service_reserved(self, other):
        for own in self.info.get('services'):
            if (own.get('type') == other.get('type') and
                    own.get('name') == other.get('name') and
                    own.get('start_value') == other.get('start_value') and
                    own.get('end_value') == other.get('end_value')):
                return True

        return False
    
    def is_netif_service_reserved(self, other):
        for own in self.info.get('services'):
            if ((own.get('from_server_interface_name') ==
                    other.get('from_server_interface_name')) and
                (own.get('to_network_interface_id') ==
                    other.get('to_network_interface_id')) and
                (own.get('to_network_interface_port') ==
                    other.get('to_network_interface_port'))):
                return True

        return False
    
    def is_reserved(self):
        for cres in self.table.find({'network_name': self.info['network_name'],
                                     'hostname': self.info['hostname'],
                                     'name': self.info['name'],
                                     'node': self.info['node'], }):
            logger.debug("We have a match, ID: %s" % (cres.get('_id'),))
            for service in cres.get('services'):
                service_type = service.get('service_type')
                if (service_type == "Range" and
                        self.is_range_service_reserved(service)):
                    return True
                elif (service_type == "NetworkInterface" and
                        self.is_netif_service_reserved(service)):
                    return True

        logger.debug("The resource is not reserved yet.")
        return False
    
    def insert(self, rm_uuid, network_name, hostname, name,
               component_id, component_manager_id, component_name, exclusive,
               system_type='', system_distribution='', system_version='',
               cpus_number=0, cpu_frequency=0,
               country='', latitude='', longitude='',
               virtualization='', memory=0, hdd_space_GB=0, agent_url='',
               services=Services().get()):
        node = {'component_id': component_id,
                'component_manager_id': component_manager_id,
                'component_name': component_name,
                'exclusive': exclusive}
        operating_system = {'type': system_type,
                            'distribution': system_distribution,
                            'version': system_version}
        cpu = {'number': cpus_number,
               'frequency': cpu_frequency}
        location = {'country': country,
                    'latitude': latitude,
                    'longitude': longitude}
        row = {'rm_uuid': rm_uuid,
               'network_name': network_name,
               'node': node,
               'hostname': hostname,
               'name': name,
               'operating_system': operating_system,
               'virtualization_technology': virtualization,
               'cpu': cpu,
               'memory': memory,
               'hdd_space_GB': hdd_space_GB,
               'agent_url': agent_url,
               'location': location,
               'services': services}
        # Return the ID of the new entry
        return self.table.insert(row)
    
    def delete(self, rm_uuid, network_name, hostname, name,
               component_id, component_manager_id, component_name, exclusive):
        node = {'component_id': component_id,
                'component_manager_id': component_manager_id,
                'component_name': component_name,
                'exclusive': exclusive}
        row = {'rm_uuid': rm_uuid,
               'network_name': network_name,
               'node': node,
               'hostname': hostname,
               'name': name}
        self.table.remove(row)
