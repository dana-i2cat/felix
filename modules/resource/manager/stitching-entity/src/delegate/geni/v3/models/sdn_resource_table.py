import pymongo


class Ports(object):
    def __init__(self):
        self.__ports = []
    
    def get(self):
        return self.__ports
    
    def add(self, name, num):
        port = {'name': name,
                'num': num}
        self.__ports.append(port)

class SDNDatapathResourceTable(object):
    def __init__(self):
        self.table = pymongo.MongoClient().felix_ro.SDNDatapathResourceTable
    
    def insert(self, rm_uuid, component_id, component_manager_id, dpid,
               ports=Ports().get()):
        row = {'rm_uuid': rm_uuid,
               'component_id': component_id,
               'component_manager_id': component_manager_id,
               'dpid': dpid,
               'ports': ports}
        # Return the ID of the new entry
        return self.table.insert(row)
    
    def delete(self, rm_uuid, component_id, component_manager_id, dpid):
        row = {'rm_uuid': rm_uuid,
               'component_id': component_id,
               'component_manager_id': component_manager_id,
               'dpid': dpid}
        self.table.remove(row)

class SDNLinkResourceTable(object):
    def __init__(self):
        self.table = pymongo.MongoClient().felix_ro.SDNLinkResourceTable
    
    def insert(self, rm_uuid, dstDPID, dstPort, srcDPID, srcPort):
        row = {'rm_uuid': rm_uuid,
               'dstDPID': dstDPID,
               'dstPort': dstPort,
               'srcDPID': srcDPID,
               'srcPort': srcPort}
        # Return the ID of the new entry
        return self.table.insert(row)
    
    def delete(self, rm_uuid, dstDPID, dstPort, srcDPID, srcPort):
        row = {'rm_uuid': rm_uuid,
               'dstDPID': dstDPID,
               'dstPort': dstPort,
               'srcDPID': srcDPID,
               'srcPort': srcPort}
        self.table.remove(row)
