import pymongo


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
