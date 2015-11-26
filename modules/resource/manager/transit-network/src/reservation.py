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
import sys
import log
import re
# import amsoil.core.log
# logger = amsoil.core.log.getLogger('TN-RM:reservation')
logger = log.getLogger('tnrm:reservation')

from datetime import datetime, timedelta, time
from xml.etree.ElementTree import *
from config import Config, Node, Interface

rspec_base = "{http://www.geni.net/resources/rspec/3}"
sharedvlan_base = "{http://www.geni.net/resources/rspec/ext/shared-vlan/1}"

# manifest_rspec = """<?xml version="1.1" encoding="UTF-8"?>
manifest_rspec = """
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

bond_str = "--x--"
config = None
pmatch = re.compile("\+([^+?]+)\?vlan=([\d]+)-([^+?]+)\?vlan=([\d]+)")
stp_head = "urn:publicid:IDN+fms:aist:tnrm+stp+"

mlink = re.compile("([\s]*<[^>]+>)")
islink = re.compile("([\s]*<[\s]*link[^>]+)>")
isvlan = re.compile("vlan=([\d]+)")

from datetime import datetime, timedelta
epoch = datetime.utcfromtimestamp(0)

def unix_time_sec(dt):
    delta = dt - epoch
    # logger.debug("timezone=%s" % (dt.tzinfo))
    return int(delta.total_seconds())

def get_config():
    return config

class Advertisement:
    def __init__(self):
        self.advertisement = config.get_advertisement()

    def get_advertisement(self):
        return self.advertisement

class Request:
    def __init__(self, slice_urn, request, start_time, end_time):
        self.slice_urn = slice_urn
        self.request = request
        self.eros = {}
        self.metrics = {}
        self.start_time = start_time
        self.end_time = end_time
        self.manifest = re.sub('<rspec [^>]+>', manifest_rspec, request)
        mlist = mlink.findall(self.manifest)

        s = ""
        for x in mlist:
            y = islink.findall(x)
            if len(y) == 1:
                z = isvlan.findall(x)
                if len(z) >= 1:
                    s += "%s vlantag=\"%s\">" % (y[0], z[0])
                else:
                    s += "%s" % (y[0])
            else:
                s += "%s" % (x)
        self.manifest = s
        
        self.urns = [] 
        self.dict_paths = {}
        self.dict_vpaths = {}
        self.dict_reservations = {}
        # logger.debug("manifest=%s" % self.manifest)

    def parse_reservations(self):
        index = 0
        rspec = fromstring(self.request)
        # tree = parse(self.request)
        # rspec = tree.getroot()

        # elem_node = rspec.find(rspec_base + "node")
        # print elem_node.tag
        # print elem_node.keys()
        # print elem_node.items()
        # if elem_node is None:
        #       raise tnex.RspecException("reservtion:parse", "There is no node spec in request spec.")
        #       return (self, "There is no node spec in request spec.")

        for elem_node in rspec.findall(rspec_base + "node"):
            node_id = elem_node.get("client_id")
            manager_id = elem_node.get("component_manager_id")
            node = Manager(node_id, manager_id)
            # logger.debug("rspec:node:manager: %s" % (node))

            sep = None;
            dep = None;

            for intf in elem_node.findall(rspec_base + "interface"):
                # logger.debug("rspec interface key=%s" % (intf.keys()))
                ep_name = intf.get("client_id")
                # logger.debug("rspec interface client_id=%s" % (ep_name))
                sharedvlan = intf.find("{http://www.geni.net/resources/rspec/ext/shared-vlan/1}link_shared_vlan")
                # logger.debug("rspec interface charedvlan=%s" % (sharedvlan))
        
                if (sharedvlan != None):
                    ep_vlantag = sharedvlan.get("vlantag")
                else:
                    ep_vlantag = None
                # logger.debug("rspec:interface id=%s, vlan=%s" % (ep_name, ep_vlantag))

                stp = config.get_nsi_stp(ep_name)
                # if stp is None, raise Exception from config

                ep = Endpoint(ep_name, ep_vlantag, node, stp)

                if sep is None:
                    sep = ep
                    continue
                if dep is None:
                    dep = ep
                    break
                
            # key = dep.name + bond_str + sep.name;
            # if key in self.dict_paths:
            #     return (self, "There is duplicate path in request spec.")
            # key = sep.name + bond_str + dep.name;
            # if key in self.dict_paths:
            #     return (self, "There is duplicate path in request spec.")
            # self.dict_paths[key] = Path(sep, dep, node)

            key = "%s?vlan=%s%s%s?vlan=%s" % (dep.name, dep.vlantag, bond_str, sep.name, sep.vlantag)
            if key in self.dict_vpaths:
                return (self, "There is duplicate vpath in request spec.")
            key = "%s?vlan=%s%s%s?vlan=%s" % (sep.name, sep.vlantag, bond_str, dep.name, dep.vlantag)
            if key in self.dict_vpaths:
                return (self, "There is duplicate vpath in request spec.")
            self.dict_vpaths[key] = Path(sep, dep, node)
            # print "add vpaths key=%s, path=%s" % (key, self.dict_vpaths[key])

        for elem_link in rspec.findall(rspec_base + "link"):
            ep1 = None
            ep2 = None
            vlan1 = None
            vlan2 = None

            link_id = elem_link.get("client_id")
            m = pmatch.findall(link_id)
            if m is not None and len(m) == 1 and len(m[0]) == 4:
                ep1 = stp_head + m[0][0]
                vlan1 = m[0][1]
                ep2 = stp_head + m[0][2]
                vlan2 = m[0][3]
                # logger.debug("%s?vlan1=%s, %s?vlan2=%s" % (ep1, vlan1, ep2, vlan2))
                # print ("%s?vlan=%s, %s?vlan=%s" % (ep1, vlan1, ep2, vlan2))

            else:
                return (self, "bad <link clinet_id=%s>" % (link_id))
                
            component_manager = elem_link.find(rspec_base + "component_manager")
            manager_name = component_manager.get("name")
            link = Manager(link_id, manager_name)
            # logger.debug("rspec:link manager: %s" % (link))

            sep_name = None;
            dep_name = None;
            sep_vlan = None;
            dep_vlan = None;

            for intf in elem_link.findall(rspec_base + "interface_ref"):
                # logger.debug("rspec interface_ref key=%s" % (intf.keys()))
                ep_name = intf.get("client_id")
                # logger.debug("rspec interface_ref client_id=%s" % (ep_name))

                if sep_name is None:
                    sep_name = ep_name;
                    if sep_name == ep1:
                        sep_vlan = vlan1
                    elif sep_name ==ep2:
                        sep_vlan = vlan2
                    continue
                if dep_name is None:
                    dep_name = ep_name;
                    if dep_name == ep1:
                        dep_vlan = vlan1
                    elif dep_name == ep2:
                        dep_vlan = vlan2
                    break

            path = None
            # key = sep_name + bond_str + dep_name;
            pathkey = "%s?vlan=%s%s%s?vlan=%s" % (sep_name, sep_vlan, bond_str, dep_name, dep_vlan)
            # print pathkey
            if pathkey in self.dict_vpaths:
                path = self.dict_vpaths[pathkey]
            if path is None:
                # key = dep_name + bond_str + sep_name;
                pathkey = "%s?vlan=%s%s%s?vlan=%s" % (dep_name, dep_vlan, bond_str, sep_name, sep_vlan)
                # print pathkey
                if pathkey in self.dict_vpaths :
                    path = self.dict_vpaths[pathkey]

            if path is None:
                return (self, "This connection is not found in <node>. %s?vlan=%s, %s?vlan=%s" %
                        (dep_name, dep_vlan, sep_name, sep_vlan))

            path.link_manager = link

            # not used now
            # only check here

            for ipro in elem_link.findall(rspec_base + "property"):
                # logger.debug("rspec interface_ref key=%s" % (ipro.keys()))
                ssep_name = ipro.get("source_id")
                ssep_vlan = "0"
                if sep_name == ssep_name:
                    ssep_vlan = sep_vlan
                elif dep_name == ssep_name:
                    ssep_vlan = dep_vlan

                ddep_name = ipro.get("dest_id")
                ddep_vlan = "0"
                if sep_name == ddep_name:
                    ddep_vlan = sep_vlan
                elif dep_name == ddep_name:
                    ddep_vlan = dep_vlan

                capacity = ipro.get("capacity")
                # logger.debug("link property src=%s, dst=%s, bw=%s" % (ssep_name, ddep_name, capacity))

                path = None
                # pathkey = ssep_name + bond_str + ddep_name;
                pathkey = "%s?vlan=%s%s%s?vlan=%s" % (ssep_name, ssep_vlan, bond_str, ddep_name, ddep_vlan)
                if pathkey in self.dict_vpaths:
                    path = self.dict_vpaths[pathkey]
                    path.sd_bw = capacity
                if path is None:
                    # pathkey = ddep_name + bond_str + ssep_name;
                    pathkey = "%s?vlan=%s%s%s?vlan=%s" % (ddep_name, ddep_vlan, bond_str, ssep_name, ssep_vlan)
                    if key in self.dict_vpaths:
                        path = self.dict_vpaths[pathkey]
                        path.ds_bw = capacity
                
                if path is None:
                    return (self, "This link property is not found in <node>. dest=%s?vlan=%s, src=%s?vlan=%s" %
                            (ddep_name, ddep_vlan, ssep_name, ssep_vlan))

            # logger.debug("path= %s" % (path))

            urn = "%s:%d" % (self.slice_urn, index)
            self.urns.append(urn)
            index = index + 1
            # print "***** %s" % (str(self.urns))

            reservation = Reservation(link_id, self.slice_urn, urn, pathkey, path, self.start_time, self.end_time)
            self.dict_reservations[urn] = reservation

            if (reservation.check_vlan == False):
                return (self, "This vlan can not be allocated, dest=vlan=%s, src=%s" %
                        (ddep_vlan, ssep_vlan))

            if (reservation.service is None):
                return (self, "This service type can not be allocated, service type=%s, path=%s." 
                        % (reservation.service, path))
                        
        return (self, None)

    def get_manifest(self):
        return self.manifest

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    def get_reservation(self, urn):
        if urn in self.dict_reservations:
            return self.dict_reservations[urn]
        return None

    def get_status(self):
        status = []
        for urn in self.urns:
            r = self.dict_reservations[urn]
            s = {}
            if r.error is None:
                s = {
                    'geni_operational_status': r.ostatus,
                    'geni_expires': r.end_time,
                    'geni_allocation_status': r.astatus,
                    'geni_sliver_urn': r.path.link_manager.node_id,
                    'geni_urn': r.slice_urn,
                    }
            else:
                s = {
                    'geni_operational_status': r.ostatus,
                    'geni_expires': r.end_time,
                    'geni_allocation_status': r.astatus,
                    'geni_sliver_urn': r.path.link_manager.node_id,
                    'geni_urn': r.slice_urn,
                    'geni_error': r.error
                    }
            status.append(s)
            # logger.debug("status:%s" % (s))
        return status

    def clear_error_status(self):
        status = []
        for urn in self.urns:
            r = self.dict_reservations[urn]
            r.error = None

    def __str__(self):
        s = None
        i = 1
        for r in self.dict_reservations.values():
            if s is None:
                s = ""
            else:
                s += "\n"
            s +=  "***** reservation %d: ***** \n" % (i)
            i += 1
            s += "%s" % (r)

        return s

class Reservation:
    def __init__(self, link_id, slice_urn, urn, pathkey, path, start_time, end_time):
        self.gid = link_id
        self.slice_urn = slice_urn
        self.urn = urn
        self.pathkey = pathkey
        self.path = path
        self.start_time = start_time
        self.end_time = end_time
        self.src_if = config.get_interface(path.sep.name)
        self.src_check = self.src_if.check_vlan(path.sep.vlantag)
        self.dst_if = config.get_interface(path.dep.name)
        self.dst_check = self.dst_if.check_vlan(path.dep.vlantag)

        self.check_vlan = False
        if (self.src_check == True and self.dst_check == True):
            self.check_vlan = True
        self.service = self.path.service

        self.ostatus = None
        self.astatus = None
        self.action = None
        self.error = None
        self.resv_id = None
        self.eroEP = None

    def settime(self, start_time, end_time):
        if start_time != 0:
            self.start_time = start_time
        if end_time != 0:
            self.end_time = end_time

    def __str__(self):
        s = "Reservation: %s/%s,%s/vlan=%s/bw=%s, %s/vlan=%s/bw=%s" % (self.slice_urn, self.urn, self.path.sep.stp, self.path.sep.vlantag, self.path.sd_bw, self.path.dep.stp, self.path.dep.vlantag, self.path.ds_bw)

        # start = datetime(1970, 1, 1) + timedelta(self.start_time/(3600*24), self.start_time%(3600*24))
        # end = datetime(1970, 1, 1) + timedelta(self.end_time/(3600*24), self.end_time%(3600*24))
        s += " time From %s" % (self.start_time)
        s += " To %s" % (self.end_time)
        # s += " From %s To %s" % (start, end)
        s += ", resvID= %s" % (self.resv_id)
        s += ", check_vlan= %s" % (self.check_vlan)
        s += ", service type= %s" % (self.service)
        return s

class Manager:
    def __init__(self, node, manager):
        self.node_id = node
        self.manager_id = manager

    def __str__(self):
        return "Manager:" + self.node_id + ":" + self.manager_id

class Endpoint:
    def __init__(self, name, vlantag, node, stp):
        self.name = name
        self.vlantag = vlantag
        self.node = node
        self.stp = stp

        self.service = "NSI"
        if ((":GRE:" in  self.name) or (":gre:" in  self.name)):
            self.service = "GRE"

        logger.info("Endpoint:name=%s, vlan=%s, node=%s, stp=%s, service type=%s" % 
                    (self.name, self.vlantag, self.node, self.stp, self.service))

    def __str__(self):
        return "Endpoint:" + self.name + ":" + self.vlantag

class Path:
    def __init__(self, sep, dep, node_manager):
        self.sep = sep
        self.dep = dep
        self.node_manager = node_manager
        self.link_manager = None
        self.sd_bw = None
        self.ds_bw = None
        self.service = None

        if (sep.service == "GRE" and dep.service == "GRE"):
            self.service = "GRE"
        if (sep.service == "NSI" and dep.service == "NSI"):
            self.service = "NSI"

    def __str__(self):
        return "Path: %s -> %s bw=%s, %s" % (self.sep.name, self.dep.name, self.sd_bw, self.ds_bw)

if __name__ == "__main__":
    config = Config("config.xml")
    # file = Request("test/request.xml")
    # file = open("request.ro.xml").read()
    file = open("test/req-test-gre.xml").read()
    start_time = datetime.utcnow()
    start_time_sec = unix_time_sec(start_time)
    end_time = start_time + timedelta(seconds=600)
    end_time_sec = unix_time_sec(end_time)

    r = Request("TEST001", file, start_time, end_time)

    resv = None
    (resv, error) = r.parse_reservations()
    if error is not None:
        print error
    if resv is not None:
        print resv
    else:
        logger.error('The request rspec can not be parsed.')

else:
    config = Config("/home/okazaki/AMsoil/tnrm/src/vendor/tnrm/config.xml")
    # config = Config("src/vendor/tnrm/config.xml")
    # r = Request("src/vendor/tnrm/request.xml")
