# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#import amsoil.core
#import amsoil.core.log
#logger = amsoil.core.log.getLogger('tnrmgeniv3delegate')
#logger = amsoil.core.log.getLogger('tnrm-config')

from xml.etree.ElementTree import *

isRead = False

advertisement_rspec = """<?xml version="1.1" encoding="UTF-8"?>
<rspec type="advertisement"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://www.geni.net/resources/rspec/3/ad.xsd
                          http://www.geni.net/resources/rspec/ext/shared-vlan/1/ad.xsd">

"""
close_rspec = '</rspec>\n'
space4 = "    "

#
dict_nodes = {}
dict_interfaces = {}
dict_nsi_stps = {}
#

class TNRM_Exception:
    def __init__(self, reason):
        self.reason = reason
        
    def __str__(self):
        return self.reason

class Config:
    def __init__(self, file):
        self.advertisement = ""
        # tree = fromstring(text)
        tree = parse(file)
        elem = tree.getroot()
        
        # elem = elem.find("resources")
        for node in elem.findall("node"):
            component_id = node.get("component_id")
            manager_id = node.get("component_manager_id")
            isExclusive = node.get("exclusive")
            felix_stps = {}
            #
            # print "add node id=" + component_id
            cnode = Node(component_id, manager_id, isExclusive, felix_stps)
            
            for ifs in node.findall("interface"):
                felix_domain_id = ifs.get("felix_domain_id")
                felix_stp_id = ifs.get("felix_stp_id")
                nsi_stp_id = ifs.get("nsi_stp_id")
                nsi_stp_id_in = ifs.get("nsi_stp_id_in")
                nsi_stp_id_out = ifs.get("nsi_stp_id_out")
                vlan = ifs.get("vlan")
                capacity = ifs.get("caoacity")
                #
                cinterface = Interface(cnode, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlan, capacity)
                felix_stps[cinterface.component_id] = cinterface

    def get_advertisement(self):
        if (self.advertisement != ""):
            return self.advertisement
        
        s = advertisement_rspec
        for cnode in dict_nodes.values():
            s += cnode.get_open_advertisement();

            for ifs in cnode.interfaces.values():
                s += ifs.get_advertisement()
            
            s += cnode.get_close_advertisement();

        s += close_rspec
        self.advertisement = s
        return self.advertisement

    def get_node(self, id):
        if (isinstance(id, type(None))):
            raise TNRM_Exception("Node Component Id is None.")

        try:
            tnode = dict_nodes[id]
            if (isinstance(tnode, type(None))):
                raise TNRM_Exception("Node Component Id does not exist. Id=%s" % id)
            else:
                return tnode
        except KeyError:
            print "Node Component Id does not exist. Id=%s" % id
        return  None

    def get_interface(self, id):
        if (isinstance(id, type(None))):
            raise TNRM_Exception("Node Component Id is None.")
        try:
            ifs = dict_interfaces[id]
            if (isinstance(ifs, type(None))):
                raise TNRM_Exception("Interface Component Id does not exist. Id=%s" % id)
            else:
                return ifs
        except KeyError:
            print "Interface Component Id does not exist. Id=%s" % id
        return  None

    def get_stp(self, id):
        if (isinstance(id, type(None))):
            raise TNRM_Exception("Node Component Id is None.")
        try:
            ifs = dict_interfaces[id]
            if (isinstance(ifs, type(None))):
                raise TNRM_Exception("Interface Component Id does not exist. Id=%s" % id)
            else:
                return ifs.nsi_stp_id
        except KeyError:
            print "Interface Component Id does not exist. Id=%s" % id
        return  None


class Node:
    def __init__(self, component_id, manager_id, isExclusive, interfaces):
        # print self, component_id, manager_id, isExclusive, interfaces
        self.component_id = component_id
        self.manager_id = manager_id
        self.isExclusive = isExclusive
        self.interfaces = interfaces
        if (isinstance(component_id, type(None))):
            raise TNRM_Exception("Node Component Id is None.")
        try:
            tnode =  dict_nodes[component_id]
            if (isinstance(tnode, type(None))):
                # print "Add #1 Node Component Id=" + component_id
                dict_nodes[component_id] = self
            else:
                print "Node Component Id is duplicate. Id=" + component_id
                # raise TNRM_Exception("Node Component Id is duplicate. Id=" + component_id)
                pass
        except KeyError:
            # print "Add #2 Node Component Id=" + component_id
            dict_nodes[component_id] = self

    def get_open_advertisement(self):
        s =  space4 + "<node component_id=\"" + self.component_id + "\"\n"
        s += space4 + "      component_manager_id=\"" + self.manager_id + "\"\n"
        s += space4 + "      exclusive=\"" + self.isExclusive + "\">\n\n"
        return s

    def get_close_advertisement(self):
        s =  space4 + "</node>\n"
        return s;

class Interface:
    def __init__(self, node, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlan, capacity):
        # print self, node, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlan, capacity
        self.node = node
        self.felix_domain_id = felix_domain_id
        self.felix_stp_id = felix_stp_id
        self.nsi_stp_id = nsi_stp_id
        self.nsi_stp_id_in = nsi_stp_id_in
        self.nsi_stp_id_out = nsi_stp_id_out
        self.vlan = vlan
        self.capacity = capacity
        self.component_id = felix_domain_id + "+" + felix_stp_id
        self.advertisement = ""
        #
        if (self.component_id == ""):
            raise TNRM_Exception("Felix Component Id is null.")
        # print "add interface=" + self.component_id + "."
        dict_interfaces[self.component_id] = self
        #
        if (self.nsi_stp_id == ""):
            raise TNRM_Exception("NSI STP Name is null.")
        else:
            dict_nsi_stps[self.nsi_stp_id] = self
        #
        if (self.nsi_stp_id_in != ""):
            dict_nsi_stps[self.nsi_stp_id_in] = self
        if (self.nsi_stp_id_out != ""):
            dict_nsi_stps[self.nsi_stp_id_out] = self

    def get_advertisement(self):
        if (self.advertisement != ""):
            return self.advertisement

        s = space4 + space4 + "<interface component_id=\"" + self.component_id +"\">\n"

        if (isinstance(self.vlan, type(None)) != True):
            s += space4 + space4 + space4 + "<sharedvlan:available name=\"" + self.component_id + "+vlan\" description=\"" + self.vlan + "\"/>\n"

        s += space4 + space4 + "</interface>\n\n"

        self.advertisement = s
        return self.advertisement

if __name__ == "__main__":
    c = Config("config.xml")
    print "adv rspec=", c.get_advertisement()
