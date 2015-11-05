#! /usr/bin/python                                                                    
#                                                                                     
# -*- coding: utf-8 -*-                                                               

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


import amsoil.core.log
logger = amsoil.core.log.getLogger('TN-RM:ovsif')
# import log
# logger = log.getLogger('tnrm:ovsgre')

import urllib
import urllib2
import json

from tn_rm_exceptions import ManagerException, ParamException

PREFIX_DEV = "tnrm"

def get_port(urlbase, dpid, tnrmp, name):
    # url = "http://localhost:8080/ovsdb/0000000000000010/ports"
    # tnrmp["ovsdb"] = address pvsdb 

    params = {}
    url = "%s/ovsdb/%s/%s" % (urlbase, dpid, "ports")
    logger.info("get_port: url=%s" % url)

    params["tnrm"] = tnrmp
    logger.info("get_port: request url=%s, dict=%s" % (url, params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        rc = json.load(rs)
        logger.info("get_port: reply dict=%s" % rc)
    except Exception as ex:
        raise ManagerException("ovsif:get_port", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))
    try:
        port = rc["tnrm"]["ports"][name]
        logger.info("get_port: ovs ofport=%s" % port)
        return port
    except:
        raise ManagerException("ovsif:get_port", 
                               "This port (%s) dose not exist in Open vSwitch(%s)." % (name, dpid))

def get_tunnel_info(urlbase, dpid, tnrmp):
    # url = "http://localhost:8080/ovsdb/0000000000000010/info"
    # tnrmp["ovsdb"] = address ovsdb 
    # tnrmp["remote_ip"] = tunnel remote address
    # tnrmp["local_ip"] = tunnel local address

    params = {}
    url = "%s/ovsdb/%s/%s" % (urlbase, dpid, "ports")
    logger.info("get_tunnel_info: url=%s" % url)

    tnrmp["name"] = PREFIX_DEV
    params["tnrm"] = tnrmp
    logger.info("get_tunnel_info: request url=%s, dict=%s" % (url, params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        rc = json.load(rs)
        logger.info("get_tunnel_info: reply dict=%s" % rc)
    except Exception as ex:
        raise ManagerException("ovsif:get_tunnel_info", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))

    ports = {}
    try:
        for p in rc["tnrm"]["ports"].keys():
            if tnrmp["name"] in p:
                logger.info("get_tunnel_info: dev=%s, port=%s" % (p, rc["tnrm"]["ports"][p]))
                ports[p] = rc["tnrm"]["ports"][p]

    except:
        # raise ManagerException("ovsif:get_tunnel_port", 
        #                        "This port (%s) dose not exist in Open vSwitch(%s)." % (name, dpid))
        logger.info("get_tunnel_info: This port (%s) dose not exist in Open vSwitch(%s)." % 
                    (tnrmp["name"], dpid))
        return ports

    find = {}
    for p in ports:
        url = "%s/ovsdb/%s/%s" % (urlbase, dpid, "tunnel/info")
        logger.info("get_tunnel_info: url=%s" % url)


        param = {}
        tnrmp["name"] = p
        param["tnrm"] = tnrmp

        logger.info("get_tunnel_info: request url=%s, dict=%s" % (url, params))

        rc = None
        try:
            req = urllib2.Request(url, "%s" % json.dumps(params))
            rs = urllib2.urlopen(req)
    
            rc = json.load(rs)
        except Exception as ex:
            raise ManagerException("ovsif:get_tunnel_info", 
                                   "error in call ryu-manager. url=%s, ex=%s" % (url, ex))
            
        tp = rc["tnrm"]["tunnel"]
        logger.info("get_tunnel_info: reply dict=%s" % tp)

        
        if tnrmp.has_key("remote_ip") and tnrmp["remote_ip"] != tp["remote_ip"]:
            pass
        elif tnrmp.has_key("type") and tnrmp["type"] != tp["type"]:
            pass
        else:
            logger.info("get_tunnel_info: find name=%s, remote_ip=%s, type=%s, port=%s" % 
                        (p, tp["remote_ip"], tp["type"], ports[p]))
            find[p] = ports[p]
    return find

def add_tunnel(urlbase, dpid, tnrmp):
    # url = "http://localhost:8080/ovsdb/0000000000000010/tunnel/create"
    # tnrmp["ovsdb"] = address pvsdb 
    # tnrmp["name"] = name of gre tunnel
    # tnrmp["type"] = "gre"
    # tnrmp["local_ip"] = local ip address
    # tnrmp["remote_ip"] = remote ip address

    params = {}
    url = "%s/ovsdb/%s/%s" % (urlbase, dpid, "tunnel/create")
    logger.info("add_tunnel: url=%s" % url)

    params["tnrm"] = tnrmp
    logger.info("add_tunnel: request url=%s, dict=%s" % (url, params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        rc = json.load(rs)
        logger.info("add_tunnel: reply dict=%s" % rc)
    except Exception as ex:
        raise ManagerException("ovsif:add_tunnel", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))

    port = rc["tnrm"]["tunnel"]["ofport"]
    logger.info("add_tunnel: ovs ofport=%s" % port)
    return port

def del_tunnel(urlbase, dpid, tnrmp):
    # url = "http://localhost:8080/ovsdb/0000000000000010/tunnel/delete"
    # tnrmp["ovsdb"] = address pvsdb 
    # tnrmp["remote_ip"] = remote ip address

    params = {}
    url = "%s/ovsdb/%s/%s" % (urlbase, dpid, "tunnel/delete")
    logger.info("delete_tunnel: url=%s" % url)
    
    params["tnrm"] = tnrmp
    logger.info("delete_tunnel: request url=%s, dict=%s" % (url,params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        rc = json.load(rs)
        logger.info("delete_tunnel: reply dict=%s" % rc)

    except Exception as ex:
        raise ManagerException("ovsif:del_tunnel", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))

def add_flow(urlbase, params):
    # url = "http://localhost:8080/stats/flowentry/add
    # params["dpid"] = int dpid of open vSwitch
    # params["match"] = {"in_port":1, "dl_vlan":1795}
    # params["action"] = [{"type":"SET_VLAN_VID", "vlan_vid":795}, {"type":"OUTPUT", "port":2}]' 
    #
    # params["priority"] = priority: matching precedence of the ow entry. int
    # params["idel_timeout"] = 0 not expired
    # params["hard_timeout"] = 0 not expired
    # params["cookie"] = 1 : opaque data value chosen by the controller. 
    #                   May be used by the controller to lter owstatistics, 
    #                   ow modication and ow deletion. Not used when processing packets. int 0
    # params["cookie_mask"] = 0
    # params["table_id"] = 0 , Table 0 signies the rst table in the pipeline.
    # params["flags"] = 1, Send flow removed message when flow expires or is deleted.

    url = "%s/stats/flowentry/add" % (urlbase)
    logger.info("add_flow: url=%s" % url)

    logger.info("add_flow: request url=%s, dict=%s" % (url, params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        logger.info("flow entry: return=%s" % rs)

        url = "%s/stats/flow/%d" % (urlbase, params['dpid'])
        rs = urllib2.urlopen(url)

        rc = json.load(rs)
        logger.info("flow entry: reply dict=%s" % rc)
    except Exception as ex:
        raise ManagerException("ovsif:add_flow", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))
    return rc

def del_flow(urlbase, params):
    url = "%s/stats/flowentry/delete" % (urlbase)
    logger.info("del_flow: url=%s" % url)

    logger.info("del_flow: request url=%s, dict=%s" % (url, params))

    rc = None
    try:
        req = urllib2.Request(url, "%s" % json.dumps(params))
        rs = urllib2.urlopen(req)

        url = "%s/stats/flow/%d" % (urlbase, params['dpid'])
        rs = urllib2.urlopen(url)

        rc = json.load(rs)
        logger.info("flow entry: reply dict=%s" % rc)

    except Exception as ex:
        raise ManagerException("ovsif:del_flow", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))
    return rc

def list_flows(urlbase, params):
    url = "%s/stats/flow/%d" % (urlbase, params['dpid'])
    rc = None
    try:
        rs = urllib2.urlopen(url)

        rc = json.load(rs)
        logger.info("flow entry: reply dict=%s" % rc)

    except Exception as ex:
        raise ManagerException("ovsif:list_flow", 
                               "error in call ryu-manager. url=%s, ex=%s" % (url, ex))
    return rc

def check_flows(urlbase, params, inport, invlan):
    rc = list_flows(urlbase, params)
    dpid = str(params['dpid'])
    lists = rc[dpid]

    for list in lists:
        match = list['match']
        logger.info("check_flows: match=%s" % match)
        logger.info("check_flows: inport=%s, %d" % (inport, match['in_port']))
        logger.info("check_flows: invlan=%s, %d" % (invlan, match['dl_vlan']))
        if int(inport) == match['in_port'] and int(invlan) == match['dl_vlan']:
            return True

    return False

def list_vlans(urlbase, params):
    url = "%s/stats/flow/%d" % (urlbase, params['dpid'])
    rs = urllib2.urlopen(url)

    rc = json.load(rs)
    logger.info("flow entry: reply dict=%s" % rc)

    return rc

if __name__ == '__main__':
    urlbase = "http://172.21.100.15:8080"
    dpid = "0000000000000010"

    if False:
        tnrmp = {}
        tnrmp["ovsdb"] = "tcp:localhost:44444"
        name = "eth2"

        port = get_port(urlbase, dpid, tnrmp, name)
        print "The ofport of %s is %s" % (name, port)

    if False:
        tnrmp = {}
        tnrmp["ovsdb"] = "tcp:172.21.100.15:44444"
        # tnrmp["name"] = "tnrm" be set in get_tunnel_info.
        tnrmp["type"] = "gre"
        tnrmp["local_ip"] = "172.21.100.15"
        tnrmp["remote_ip"] = "172.22.100.15"

        ports = get_tunnel_info(urlbase, dpid, tnrmp)
        for p in ports.keys():
            pp = ports[p]
            print "The ofport of %s to %s is %s" % (pp["name"], pp["remote_ip"], pp["ofport"])

    if False:
        tnrmp = {}
        tnrmp["ovsdb"] = "tcp:localhost:44444"
        tnrmp["name"] = "tnrm001"
        tnrmp["type"] = "gre"
        tnrmp["local_ip"] = "172.21.100.15"
        tnrmp["remote_ip"] = "172.22.100.15"

        port = add_tunnel(urlbase, dpid, tnrmp)
        print "The ofport of %s to %s is %s" % (tnrmp["name"], tnrmp["remote_ip"], port)

    if False:
        tnrmp = {}
        tnrmp["ovsdb"] = "tcp:localhost:44444"
        tnrmp["name"] = "tnrm001"
        tnrmp["remote_ip"] = "172.22.100.15"

        del_tunnel(urlbase, dpid, tnrmp)
        # print "The ofport of %s is %s" % (tnrmp["name"], port)

    if False:
        tnrmp = {}
        tnrmp["dpid"] = int(dpid, 16)
        matchs = {"in_port":1, "dl_vlan":1795}
        tnrmp["match"] = matchs
        actions = [{"type":"SET_VLAN_VID", "vlan_vid":1790}, {"type":"OUTPUT", "port":2}] 
        tnrmp["actions"] = actions
        tnrmp["priority"] = 1000
        tnrmp["idel_timeout"] = 0
        tnrmp["hard_timeout"] = 0
        tnrmp["cookie"] = 1
        tnrmp["cookie_mask"] = 1
        tnrmp["table_id"] = 0
        tnrmp["flags"] = 1

        rc = add_flow(urlbase, tnrmp)
        print "add flow ret=%s" % rc

    if False:
        tnrmp = {}
        tnrmp["dpid"] = int(dpid, 16)

        rc = list_flows(urlbase, tnrmp)
        print "list flows ret=%s" % rc

    if True:
        tnrmp = {}
        tnrmp["dpid"] = int(dpid, 16)

        rc = check_flows(urlbase, tnrmp, 1, 1795)
        print "list flows ret=%s" % rc

    if False:
        tnrmp = {}
        tnrmp["dpid"] = int(dpid, 16)

        rc = list_vlans(urlbase, tnrmp)
        print "list flows ret=%s" % rc

    if False:
        tnrmp = {}
        tnrmp["dpid"] = int(dpid, 16)
        matchs = {"in_port":1, "dl_vlan":1795}
        tnrmp["match"] = matchs

        rc = del_flow(urlbase, tnrmp)
        print "delete flow ret=%s" % rc
