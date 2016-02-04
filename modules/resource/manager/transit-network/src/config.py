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

#import eisoil.core
#import eisoil.core.log
#logger = eisoil.core.log.getLogger('tnrmgeniv3delegate')
#logger = eisoil.core.log.getLogger('tnrm-config')

from xml.etree.ElementTree import *
from tn_rm_exceptions import ManagerException, ParamException, RspecException
from vlanManager import *

# from tn_rm_delegate import logger
import log
logger = log.getLogger('tnrm:config')
logger.info("config: ready")

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
default_type = "NSI"

#
dict_nodes = {}
dict_interfaces = {}
dict_nsi_stps = {}
dict_felix_stps = {}
#

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
            #
            # print "add node id=" + component_id
            cnode = Node(component_id, manager_id, isExclusive, dict_felix_stps)
            
            for ifs in node.findall("interface"):
                felix_domain_id = ifs.get("felix_domain_id")
                felix_stp_id = ifs.get("felix_stp_id")
                nsi_stp_id = ifs.get("nsi_stp_id")
                # nsi_stp_id_in = ifs.get("nsi_stp_id_in")
                # nsi_stp_id_out = ifs.get("nsi_stp_id_out")
                vlans = ifs.get("vlan")
                capacity = ifs.get("capacity")
                #
                # cinterface = Interface(cnode, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlans, capacity)
                cinterface = Interface(cnode, felix_domain_id, felix_stp_id, nsi_stp_id, vlans, capacity)
                cinterface.component_id = "%s+%s" % (felix_domain_id, felix_stp_id)
                #
                gre_type = ifs.get("type")
                gre_address = ifs.get("address")
                gre_sedev = ifs.get("sedev")
                # gre_ofport = ifs.get("ofport")
                # gre_brname = ifs.get("brname")
                gre_dpid = ifs.get("dpid")
                gre_ovsdb = ifs.get("ovsdb")
                gre_ryu = ifs.get("ryu")

                if (gre_type is not None and gre_type != default_type):
                    try:
                        # print "gre_dpid=" + gre_dpid
                        gre_dpid_i = int(gre_dpid)
                    except:
                        # try base 16
                        try:
                            gre_dpid_i = int(gre_dpid, 16)
                        except Exception as e:
                            raise ParamException("config:", "%s is not DPID_PATTERN or Integer" % (gre_dpid))

                    gre_dpid = "%016x" % gre_dpid_i
                    # print "gre_dpid=" + gre_dpid

                    # cinterface.set(gre_type, gre_address, gre_ofdev, gre_ofport, gre_brname, gre_dpid, 
                    #                gre_ovsdb, gre_ryu)
                    cinterface.set(gre_type, gre_address, gre_dpid, gre_ovsdb, gre_ryu, gre_sedev)
                    # print "**** %s" % (cinterface)
                dict_felix_stps[cinterface.component_id] = cinterface

    def get_advertisement(self):
        s = advertisement_rspec
        for cnode in dict_nodes.values():
            s += cnode.get_open_advertisement();

            for ifs in cnode.interfaces.values():
                s += ifs.get_advertisement()
            
            s += cnode.get_close_advertisement();

        s += close_rspec
        self.advertisement = s
        return self.advertisement

    def get_nsi_stp(self, id):
        if id in dict_felix_stps:
            interface = dict_felix_stps[id]
            return interface.nsi_stp_id
        raise ParamException("config:", "%s is not exist in config.xml." % (id))

    def get_node(self, id):
        if (isinstance(id, type(None))):
            raise ParamException("config:", "Node Component Id is None.")

        try:
            tnode = dict_nodes[id]
            if (isinstance(tnode, type(None))):
                raise ParamException("config:", "Node Component Id does not exist. Id=%s" % id)
            else:
                return tnode
        except KeyError:
            print "Node Component Id does not exist. Id=%s" % id
        return  None

    def get_interface(self, id):
        if (isinstance(id, type(None))):
            raise ParamException("config:", "Node Component Id is None.")
        try:
            ifs = dict_interfaces[id]
            if (isinstance(ifs, type(None))):
                raise ParamException("config:", "Interface Component Id does not exist. Id=%s" % id)
            else:
                return ifs
        except KeyError:
            print "Interface Component Id does not exist. Id=%s" % id
        return  None

    def get_stp(self, id):
        if (isinstance(id, type(None))):
            raise ParamException("config:", "Node Component Id is None.")
        try:
            ifs = dict_interfaces[id]
            if (isinstance(ifs, type(None))):
                raise ParamException("config:", "Interface Component Id does not exist. Id=%s" % id)
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
            raise ParamException("config:", "Node Component Id is None.")
        try:
            tnode =  dict_nodes[component_id]
            if (isinstance(tnode, type(None))):
                # print "Add #1 Node Component Id=" + component_id
                dict_nodes[component_id] = self
            else:
                print "Node Component Id is duplicate. Id=" + component_id
                # raise ParamException("config:", "Node Component Id is duplicate. Id=" + component_id)
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
    def __init__(self, node, felix_domain_id, felix_stp_id, nsi_stp_id, vlans, capacity):
        # def __init__(self, node, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlan, capacity):
        # print self, node, felix_domain_id, felix_stp_id, nsi_stp_id, nsi_stp_id_in, nsi_stp_id_out, vlan, capacity
        self.node = node
        self.felix_domain_id = felix_domain_id
        self.felix_stp_id = felix_stp_id
        self.nsi_stp_id = nsi_stp_id
        # self.nsi_stp_id_in = ""
        # self.nsi_stp_id_out = ""
        self.vlans = vlans
        self.capacity = capacity
        self.component_id = felix_domain_id + "+" + felix_stp_id
        self.advertisement = ""

        self.gtype = default_type
        self.address = None
        self.dpid = None
        self.ovsdb = None
        self.ryu_url = None

        self.dict_ofdev = {}
        self.dict_ofport = {}
        self.sedev = None
        self.seport = None

        self.vman = vlanManager(self.nsi_stp_id, self.vlans)

        # self.brname = None
        #
        if (self.component_id == ""):
            raise ParamException("config:", "Felix Component Id is null.")
        # print "add interface=" + self.component_id + "."
        dict_interfaces[self.component_id] = self
        #
        if (self.nsi_stp_id == ""):
            raise ParamException("config:", "NSI STP Name is null.")
        else:
            dict_nsi_stps[self.nsi_stp_id] = self
        #
        # if (self.nsi_stp_id_in != ""):
        #     dict_nsi_stps[self.nsi_stp_id_in] = self
        # if (self.nsi_stp_id_out != ""):
        #     dict_nsi_stps[self.nsi_stp_id_out] = self
        #

    # def set(self, gtype, address, ofdev, ofport, brname, dpid, ovsdb, ryu):
    def set(self, gtype, address, dpid, ovsdb, ryu, sedev):
        self.gtype = gtype
        self.address = address
        self.dpid = dpid
        self.ovsdb = ovsdb
        self.ryu_url = ryu
        self.sedev = sedev

    def set_of(self, ovs_id, ofdev, ofport):
        self.dict_ofdev[ovs_id] = ofdev
        self.dict_ofport[ovs_id] = ofport

    def unset_of(self, ovs_id):
        if self.dict_ofdev.has_key(os_id):
            del self.dict_ofdev[ovs_id]
        if self.dict_ofport.has_key(ovs_id):
            del self.dict_ofport[ovs_id]

    def get_of(self, ovs_id):
        ofdev = self.dict_ofdev[ovs_id]
        ofport = self.dict_ofport[ovs_id]
        return (ofdev, ofport)

    def get_advertisement(self):
        s = space4 + space4 + "<interface component_id=\"" + self.component_id +"\">\n"

        vlan = self.vman.getFreeList()
        if (isinstance(vlan, type(None)) != True):
            s += space4 + space4 + space4 + "<sharedvlan:available name=\"" + self.component_id + "+vlan\" description=\"" + vlan + "\"/>\n"

        s += space4 + space4 + "</interface>\n\n"

        self.advertisement = s
        return self.advertisement

    def check_vlan(self, vlans):
        try:
            logger.info("interface:check_vlan: vman: %s" % self.vman)
            logger.info("interface:check_vlan: vlans: %s" % vlans)
            dict_p = {}
            dict_p = self.vman.productAllowedVlans(vlans)
            logger.info("interface:check_vlan: productSet is %s" % dict_p)
            if len(dict_p) == 0:
                return False
            return True
        except Exception as e:
            logger.info("interface:check_vlan: Exception: %s" % e)
            return False

    def __str__(self):
        s = "node=%s, domain=%s, f_stp=%s, nsi_stp=%s, vlan=%s, capacity=%s, type=%s" % (self.node, self.felix_domain_id, self.felix_stp_id, self.nsi_stp_id, self.vlans, self.capacity, self.gtype)
        if (self.gtype != default_type):
            s += ", address=%s, ofdev=%s, ofport=%s, sedev=%s, seport=%s, dpid=%s, ovsdb=%s, ryu=%s" % (self.address, self.dict_ofdev, self.dict_ofport, self.sedev, self.seport, self.dpid, self.ovsdb, self.ryu_url)
        return s

if __name__ == "__main__":
    c = Config("config.xml")
    print "adv rspec=", c.get_advertisement()
    cid = "urn:publicid:IDN+fms:aist:tnrm+stp+urn:ogf:network:aist.go.jp:2013:topology:gre-se2"
    cif = c.get_interface(cid)
    print cif.check_vlan("1600")
    print cif.check_vlan("1700")
    print cif.check_vlan("1800")
