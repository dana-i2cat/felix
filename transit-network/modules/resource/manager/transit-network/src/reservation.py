# import amsoil.core
# import amsoil.core.log
# logger = amsoil.core.log.getLogger('tnrmgeniv3delegate')

from datetime import datetime, timedelta, time
from xml.etree.ElementTree import *
from config import Config, Node, Interface, TNRM_Exception

dict_resv = {}
dict_ep = {}

rspec_base = "{http://www.geni.net/resources/rspec/3}"
sharedvlan_base = "{http://www.geni.net/resources/rspec/ext/shared-vlan/1}"

manifest_rspec = """<?xml version="1.1" encoding="UTF-8"?>
<rspec type="manifest"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:stitch="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/
            http://hpn.east.isi.edu/rspec/ext/stitch/0.1/stitch-schema.xsd
            http://www.geni.net/resources/rspec/3/manifest.xsd
            http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">

"""
close_rspec = '</rspec>\n'
ospace4 = '    '

class Request:
    def __init__(self, request):
        self.request = request
        self.endpoints = {}
        self.start_time = 0
        self.end_time = 0

    def getReservation(self):
        rspec = fromstring(self.request)
        # tree = parse(self.request)
        # rspec = tree.getroot()
        # print rspec.tag

        elem_node = rspec.find(rspec_base + "node")
        # print elem_node.tag
        # print elem_node.keys()
        # print elem_node.items()
        node_id = elem_node.get("client_id")
        manager_id = elem_node.get("component_manager_id")
        manager = Manager(node_id, manager_id)
        self.node = config.get_node(node_id)
        # print node_id, manager_id

        for intf in elem_node.findall(rspec_base + "interface"):
            # print intf.keys()
            ep_name = intf.get("client_id")
            # print ep_name
            sharedvlan = intf.find("{http://www.geni.net/resources/rspec/ext/shared-vlan/1}link_shared_vlan")
            # print sharedvlan
            if (sharedvlan != None):
                # print sharedvlan.keys()
                ep_vlantag = sharedvlan.get("vlantag")
                # print ep_vlantag
            else:
                ep_vlantag = None
            # print ep_name, ep_vlantag
            self.endpoints[ep_name] = Endpoint(ep_name, ep_vlantag, self.node)
        
        elem_link = rspec.find(rspec_base + "link")
        # print elem_link.tag
        # print elem_link.keys()
        link_id = elem_link.get("client_id")
        component_manager = elem_link.find(rspec_base + "component_manager")
        # print component_manager.keys()
        manager_name = component_manager.get("name")
        # print link_id, manager_name

        index = 0
        property = elem_link.find(rspec_base + "property")
        # print property.keys()
        src = {}
        dst = {}
        capacity = {}
        for property in elem_link.findall(rspec_base + "property"):
            src[index] = property.get("source_id")
            dst[index] = property.get("dest_id")
            capacity[index] = property.get("capacity")
            # print index, src[index], dst[index], capacity[index]
            index += 1

        # print src, dst
        if (index != 2):
            raise TNRM_Exception("There is only a one-way property in request rspec")
        if (str(src[0]) == str(dst[1])):
            pass
        else:
            # print str(src[0]), str(dst[1])
            raise TNRM_Exception("Endpointp descriptions do not match in request rspec")
        if (src[1] != dst[0]):
            # print str(src[0]), str(dst[1])
            raise TNRM_Exception("Endpoint descriptions do not match in request rspec")
        if (capacity[0] != capacity[1]):
            # print "Since the capacity is different, select big capacity"
            if (int(capacity[0]) < int(capacity[1])):
                capacity[0] = capacity[1]

        self.ero = self.endpoints.copy()
        del self.ero[src[0]]
        del self.ero[dst[0]]
        # print "ERO: ", self.ero
        self.reservation = Reservation(self, self.node, self.endpoints[src[0]], self.endpoints[dst[0]], self.ero, capacity[0])
        # print self.reservation
        return self.reservation

class Reservation:
    def __init__(self, request, node, sep, dep, ero, capacity):
        self.request = request
        self.node = node
        self.sEP = sep
        self.dEP = dep
        # self.eroEP = []
        self.capacity = capacity
        self.sSTP = config.get_stp(self.sEP.name)
        self.dSTP = config.get_stp(self.dEP.name)
        #
        self.srcUsedVlan = ""
        self.dstUsedVlan = ""
        #
        # self.eroSTP = []
        self.eroString = ""
        for e in ero:
            # print e
            stp = config.get_stp(e)
            if (self.eroString != ""):
                self.eroString = self.eroString + "," + stp
            else:
                self.eroString = stp
            
            # self.eroSTP.append(stp)
            # self.eroEP.append[e]
        self.manifest = ""

    def set_used_vlan(self, src_used_vlan, dst_used_vlan):
        self.srcUsedVlan = src_used_vlan
        self.dstUsedVlan = dst_used_vlan

    def settime(self, start_time, end_time):
        if (start_time != 0):
            self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        s =  "Reservation:" + self.sSTP + "/" + self.dSTP + ", BW=" + self.capacity + ", ERO=" + self.eroString + ", vlan=" + self.sEP.vlantag + "/" + self.dEP.vlantag
        start = datetime(1970, 1, 1) + timedelta(self.start_time/(3600*24), self.start_time%(3600*24))
        s += " time From %s" % (start)
        end = datetime(1970, 1, 1) + timedelta(self.end_time/(3600*24), self.end_time%(3600*24))
        s += " To %s" % (end)
        return s

    def get_manifest(self):
        if (self.manifest != ""):
            return self.manifest

        s = manifest_rspec
        s += ospace4 + '<node client_id=\"' + self.node.component_id + '\" '
        s += 'component_manager_id=\"' + self.node.manager_id + '\">\n'

        for v_ep in self.request.endpoints.itervalues():
            s += ospace4 + ospace4 + '<interface client_id=\"'
            s += v_ep.name + '\">\n'
            if (isinstance(v_ep.vlantag, type(None)) != True):
                s += ospace4 + ospace4 + ospace4 
                s += '<sharedvlan:link_shared_vlan name=\"'
                s += v_ep.name + '+vlan\" '
                s += 'vlantag=\"' + v_ep.vlantag + '\"/>\n'
            s += ospace4 + ospace4 + '</interface>\n'
        s += ospace4 + '</node>\n'
        s += '\n'

        s += ospace4 + '<link client_id=\"' + self.node.component_id + ':link\" '
        s += 'vlantag=\"' + self.sEP.vlantag + '\">\n'
        s += ospace4 + ospace4
        s += '<component_manager name=\"' + self.node.manager_id + '\"/>\n'

        for v_ep in self.request.endpoints.itervalues():
            s += ospace4 + ospace4 + '<interface_ref client_id=\"'
            s += v_ep.name+ '\">\n'
            if (False and isinstance(v_ep.vlantag, type(None)) != True):
                s += ospace4 + ospace4 + ospace4 
                s += '<sharedvlan:link_shared_vlan name=\"'
                s += v_ep.name + '+vlan\" '
                s += 'vlantag=\"' + v_ep.vlantag + '\"/>\n'
            s += ospace4 + ospace4 + '</interface_ref>\n'

        s += ospace4 + ospace4 + '<property source_id=\"'
        s += self.sEP.name + '\"\n'
        s += ospace4 + ospace4 + '          dest_id=\"'
        s += self.dEP.name + '\"\n'
        s += ospace4 + ospace4 + '          capacity=\"' + self.capacity + '\">\n'
        s += ospace4 + ospace4 + '</property>\n'

        s += ospace4 + ospace4 + '<property source_id=\"'
        s += self.dEP.name + '\"\n'
        s += ospace4 + ospace4 + '          dest_id=\"'
        s += self.sEP.name + '\"\n'
        s += ospace4 + ospace4 + '          capacity=\"' + self.capacity + '\">\n'
        s += ospace4 + ospace4 + '</property>\n'

        s += ospace4 + '</link>\n'

        s += close_rspec
        self.manifest = s
        return self.manifest

class TNRM_Exception:
    def __init__(self, reason):
        self.reason = reason
        
    def __str__(self):
        return self.reason

class Manager:
    def __init__(self, node, manager):
        self.node = node
        self.manager = manager

class Endpoint:
    def __init__(self, name, vlantag, node):
        self.name = name
        self.vlantag = vlantag
        self.node = node
        # print "Endpoint:", self.name, self.vlantag, self.node

    def __str__(self):
        return "Endpoint:" + self.endpoint + ":" + self.vlantag

if __name__ == "__main__":
    config = Config("config.xml")
    # r = Request("test/request.xml")
    file = open("test/request.xml").read()
    r = Request(file)
    resv = r.get_reservation()
    print resv
    print resv.get_manifest()
else:
    config = Config("/home/okazaki/AMsoil/sdnrm/src/vendor/tnrm/config.xml")
#    config = Config("src/vendor/tnrm/config.xml")
#r = Request("src/vendor/tnrm/request.xml")


