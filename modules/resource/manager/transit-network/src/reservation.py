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

import tn_rm_exceptions as tnex
import log
logger = log.getLogger('tnrm:reservation')

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
ospace4 = '  '

class Request:
    def __init__(self, request):
        self.request = request
        self.endpoints = {}
        self.eros = {}
        self.metrics = {}
        self.node = Manager("", "")

    def getReservation(self):
        rspec = fromstring(self.request)
        # tree = parse(self.request)
        # rspec = tree.getroot()

        elem_node = rspec.find(rspec_base + "node")
        # print elem_node.tag
        # print elem_node.keys()
        # print elem_node.items()
        if elem_node is None:
            # raise tnex.RspecException("reservtion:parse", "There is no node spec in request spec.")
            logger.debug("There is no node spec in request spec.")
        else:
            node_id = elem_node.get("client_id")
            manager_id = elem_node.get("component_manager_id")
            self.node = Manager(node_id, manager_id)
            logger.debug("rspec node_id=%s, manager_id=%s" % (node_id, manager_id))

            for intf in elem_node.findall(rspec_base + "interface"):
                logger.debug("rspec interface key=%s" % (intf.keys()))

                ep_name = intf.get("client_id")
                logger.debug("rspec interface client_id=%s" % (ep_name))
                sharedvlan = intf.find("{http://www.geni.net/resources/rspec/ext/shared-vlan/1}link_shared_vlan")
                logger.debug("rspec interface charedvlan=%s" % (sharedvlan))

                if (sharedvlan != None):
                    ep_vlantag = sharedvlan.get("vlantag")
                else:
                    ep_vlantag = None
                logger.debug("rspec interface vlantag=%s" % (ep_vlantag))

                self.endpoints[ep_name] = Endpoint(ep_name, ep_vlantag, self.node)
        
        elem_link = rspec.find(rspec_base + "link")
        if elem_link is None:
            raise tnex.RspecException("reservtion:parse", "There is no link spec in request spec.")

        link_id = elem_link.get("client_id")
        component_manager = elem_link.find(rspec_base + "component_manager")
        if elem_link is None:
            logger.info('There is no lonk:component_manager) spec.')
        else:
            manager_name = component_manager.get("name")
            logger.info("link:manager name=%s" % (manager_name))

        for intf in elem_link.findall(rspec_base + "interface_ref"):
            logger.debug("rspec interface_ref key=%s" % (intf.keys()))

            ep_name = intf.get("client_id")
            logger.debug("rspec interface_ref client_id=%s" % (ep_name))

            logger.debug("rspec endpoints=%s" % (self.endpoints))
            ep = Endpoint(ep_name, "0", "")
            logger.debug("rspec ep=%s" % (ep))
            if self.endpoints.has_key(ep_name):
                logger.debug("rspec endpoints=%s" % (self.endpoints))
            else:
                logger.debug("add endpoint client_id=%s" % (ep_name))
                self.endpoints[ep_name] = ep

        property = elem_link.find(rspec_base + "property")
        if property is None:
            raise tnex.RspecException("reservtion:parse", "There is no node spec in property spec.")

        index = 0
        src = {}
        dst = {}
        capacity = {}
        for property in elem_link.findall(rspec_base + "property"):
            src[index] = property.get("source_id")
            dst[index] = property.get("dest_id")
            capacity[index] = property.get("capacity")
            logger.info("index=%s, src=%s, dst=%s, capacity=%s" % 
                        (str(index), src[index], dst[index], capacity[index]))

            path = property.find('{http://hpn.east.isi.edu/rspec/ext/stitch/0.1/}path')
            if path is None:
                self.eros[index] = None
                self.metrics[index] = None
            else:
                hops = path.findall('{http://hpn.east.isi.edu/rspec/ext/stitch/0.1/}hop')
                e = {}
                o = {}
                m = {}
                for hop in hops:
                    if hop is None:
                        continue
                    hid = int(hop.get('id')) - 1
                    hlink = hop.find('{http://hpn.east.isi.edu/rspec/ext/stitch/0.1/}link')
                    e[hid] = hlink.get('id')
                    hmetric = hlink.find('{http://hpn.east.isi.edu/rspec/ext/stitch/0.1/}trafficEngineeringMetric')
                    m[hid] = hmetric.text
                    nexthop = hop.find('{http://hpn.east.isi.edu/rspec/ext/stitch/0.1/}nextHop')
                    o[hid] = -1
                    if nexthop is not None:
                        o[hid] = int(nexthop.text) -1

                    logger.info("hop=%s, ero=%s, order=%s, metric=%s" % 
                                (str(hid), e[hid], o[hid], m[hid]))

                if len(e) == 0:
                    continue

                ee = {}
                ee[0] = e[0]
                oid = o[0]
                mm = {}
                mm[0] = m[0]
                eeid = 1
                while oid <> -1:
                    ee[eeid] = e[oid]
                    mm[eeid] = m[oid]
                    eeid += 1
                    oid = o[oid]
                    # print ee
                self.eros[index] = ee
                self.metrics[index] = mm
            index += 1

        # print src, dst
        if (index != 2):
            logger.info("index != 2, is %d" % (index))
            raise tnex.ParamException("reservtion:param", "There is only a one-way property in request rspec")
        if (src[0] != dst[1]):
            logger.info("src[0]=%s, dst[1]=%s" % (src[0]), str(dst[1]))
            raise tnex.ParamException("reservtion:param", "Endpointp descriptions do not match in request rspec")

        if (src[1] != dst[0]):
            logger.info("src[1]=%s, dst[0]=%s" % (src[1]), str(dst[0]))
            raise tnex.ParamException("reservtion:param", "Endpoint descriptions do not match in request rspec")

        if (capacity[0] != capacity[1]):
            logger.info("the capacity is different 0:=%s, 1:=%s" % (capacity[0], capacity[1]))
            # print "Since the capacity is different, select big capacity"
            if (int(capacity[0]) < int(capacity[1])):
                capacity[0] = capacity[1]
                logger.info("select capacity=%s" % (capacity[1]))
            else:
                logger.info("select capacity=%s" % (capacity[0]))

        # self.ero = self.endpoints.copy()
        # del self.ero[src[0]]
        # del self.ero[dst[0]]
        logger.info("src=%s, dst=%s" % (self.endpoints[src[0]], self.endpoints[dst[0]]))
        logger.info("ERO=%s" % (self.eros))
        logger.info("src=%s, dst=%s" % (self.endpoints[src[0]], self.endpoints[dst[0]]))
        self.reservation = Reservation(self, self.node, 
                                       self.endpoints[src[0]], self.endpoints[dst[0]], 
                                       self.eros[0], self.metrics[0], capacity[0])
        return self.reservation

class Reservation:
    def __init__(self, request, node, sep, dep, ero, metric, capacity):
        self.request = request
        self.node = node
        self.sEP = sep
        self.dEP = dep
        self.eroEP = None
        self.metric = metric
        self.capacity = capacity
        self.sSTP = config.get_stp(self.sEP.name)
        self.dSTP = config.get_stp(self.dEP.name)
        self.start_time = 0
        self.end_time = 0
        #
        # self.eroSTP = 
        #
        self.srcUsedVlan = ""
        self.dstUsedVlan = ""
        #
        logger.info("Reservation:ero=%s" % (ero))
        self.eroString = ""
        self.manifest = None

        if ero is not None:
            self.eroEP = ero.values()
            logger.info("Reserve:eroEP=%s" % (self.eroEP))

            for e in ero.keys():
                logger.info("Reserve:ero[%s]=%s" % (e, ero[e]))
                if ero[e] is None:
                    continue

                stp = config.get_stp(ero[e])
                # print "stp=", stp
                if stp is None:
                    continue

                logger.info("Reserve:STP=%s" % (stp))
                if self.eroString != "":
                    self.eroString = self.eroString + "," + stp
                else:
                    self.eroString = stp
            
                    # self.eroSTP.append(stp)
                    # self.eroEP.append[e]

        logger.info("Reservation:init done.")

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
        if (self.manifest is not None):
            return self.manifest

        s = manifest_rspec
        s += ospace4 + '<node client_id=\"' + self.node.node_id + '\" '
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

        s += ospace4 + '<link client_id=\"' + self.node.node_id + 'link\" '
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

        if self.eroEP is not None:
            s += ospace4 + ospace4 + ospace4 + '<stitch:path id=\"'
            s += self.sEP.name + "+" + self.dEP.name + '\">\n'
            size = len(self.eroEP)
            hop = 1
            for i in range(0, size):
                s += ospace4 + ospace4 + ospace4 + ospace4 + '<stitch:hop id=\"' + str(hop) + '\">\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + '<stitch:link id=\"'
                s += self.eroEP[i] + '\">\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + ospace4
                s += '<stitch:trafficEngineeringMetric>' + self.metric[i] + '</stitch:trafficEngineeringMetric>\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + '</stitch:link>\n'
                if size != hop:
                    s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4
                    s += '<stitch:nextHop>' + str(hop+1) + '</stitch:nextHop>\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + '</stitch:hop>\n'
                hop += 1
            s += ospace4 + ospace4 + ospace4 + '</stitch:path>\n'

        s += ospace4 + ospace4 + '</property>\n'

        s += ospace4 + ospace4 + '<property source_id=\"'
        s += self.dEP.name + '\"\n'
        s += ospace4 + ospace4 + '          dest_id=\"'
        s += self.sEP.name + '\"\n'
        s += ospace4 + ospace4 + '          capacity=\"' + self.capacity + '\">\n'

        if self.eroEP is not None:
            s += ospace4 + ospace4 + ospace4 + '<stitch:path id=\"'
            s += self.sEP.name + "+" + self.dEP.name + '\">\n'
            size = len(self.eroEP)
            hop = 1
            for i in range(size-1, -1, -1):
                s += ospace4 + ospace4 + ospace4 + ospace4 + '<stitch:hop id=\"' + str(hop) + '\">\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + '<stitch:link id=\"'
                s += self.eroEP[i] + '\">\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + ospace4
                s += '<stitch:trafficEngineeringMetric>' + self.metric[i] + '</stitch:trafficEngineeringMetric>\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4 + '</stitch:link>\n'
                if size != hop:
                    s += ospace4 + ospace4 + ospace4 + ospace4 + ospace4
                    s += '<stitch:nextHop>' + str(hop+1) + '</stitch:nextHop>\n'
                s += ospace4 + ospace4 + ospace4 + ospace4 + '</stitch:hop>\n'
                hop += 1
            s += ospace4 + ospace4 + ospace4 + '</stitch:path>\n'

        s += ospace4 + ospace4 + '</property>\n'
        s += ospace4 + '</link>\n'

        s += close_rspec
        self.manifest = s
        return self.manifest

class Manager:
    def __init__(self, node, manager):
        self.node_id = node
        self.manager_id = manager

class Endpoint:
    def __init__(self, name, vlantag, node):
        self.name = name
        self.vlantag = vlantag
        self.node = node
        logger.info("Endpoint:name=%s, vlan=%s, node=%s" % (self.name, self.vlantag, self.node))

    def __str__(self):
        return "Endpoint:" + self.name + ":" + self.vlantag

if __name__ == "__main__":
    config = Config("config.xml")
    # file = Request("test/request.xml")
    # file = open("request.v1.xml").read()
    file = open("request.ro.xml").read()
    r = Request(file)

    resv = None
    try:
        resv = r.getReservation()
    except tnex.RspecException:
        logger.error('getReservation()')

    if resv is not None:
        print resv
        print resv.get_manifest()
    else:
        logger.error('The request rspec can not be parsed.')

else:
    config = Config("/home/okazaki/AMsoil/sdnrm/src/vendor/tnrm/config.xml")
    # config = Config("src/vendor/tnrm/config.xml")
    # r = Request("src/vendor/tnrm/request.xml")
