#! /usr/bin/python
#

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

import json
import re

from webob import Response
from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib.dpid import DPID_PATTERN, dpid_to_str, str_to_dpid

from ryu.lib.ovs import bridge

OVSDB_IP1 = 'tcp:172.21.100.15:44444'
OVSDB_IP2 = 'tcp:172.22.100.15:44444'

# HEX_PATTERN = r'0x[0-9a-z]+'
# DIGIT_PATTERN = r'[1-9][0-9]*'
NAME_PATTERN = r'[1-9a-zA-Z]*'
OVS_NAME_BASE = "tnrm"

class GreTnrmController(app_manager.RyuApp):

    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        print "GreTnrmController:__init__"
        super(GreTnrmController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(GreTnrmAPI, {'GreTnrmController' : self})

    def list_ports(self, dpid, params):
        ovsdb = params['tnrm']['ovsdb']

        id = int(dpid, 16)
        print "id=%d" % id 
        ovs_bridge = bridge.OVSBridge(bridge.CONF, id, ovsdb)

        ovs_bridge.init()
        ports = ovs_bridge.get_port_name_list()
        # results = []
        results = {}
        for p in ports:
            ofport = ovs_bridge.get_ofport(p)
            # print "ports=%s ofport=%d" % (p, ofport)
            result = {'port': '%s' % p, 'ofport': '%d' % ofport}
            # results.append(result)
            results[p] = str(ofport)

        return ({'id': '%s' % id, 'tnrm': {'ports': results }})
            
    def tunnel_info(self, dpid, params):
        ovsdb = params['tnrm']['ovsdb']
        tunnel_type = params['tnrm']['type']
        tunnel_name = params['tnrm']['name']

        id = int(dpid, 16)
        ovs_bridge = bridge.OVSBridge(bridge.CONF, id, ovsdb)

        try:
            ovs_bridge.init()
            print "%s, %s" % (tunnel_name, tunnel_type)
            tp = ovs_bridge.get_tunnel_port(tunnel_name, tunnel_type)
        except:
            raise

        output = { 'id': '%d' % id,
                   'tnrm': { 'tunnel': { 'name': '%s' % tp.port_name,
                                         'ofport': '%s' % tp.ofport,
                                         'type': '%s' % tp.tunnel_type,
                                         'local_ip': '%s' % tp.local_ip,
                                         'remote_ip': '%s' % tp.remote_ip }}}
        return output

    def tunnel_create(self, dpid, params):
        ovsdb = params['tnrm']['ovsdb']
        remote_ip = params['tnrm']['remote_ip']
        local_ip = params['tnrm']['local_ip']
        tunnel_type = params['tnrm']['type']
        tunnel_name = params['tnrm']['name']

        id = int(dpid, 16)
        ovs_bridge = bridge.OVSBridge(bridge.CONF, id, ovsdb)

        try:
            ovs_bridge.init()
            ovs_bridge.add_tunnel_port(tunnel_name, tunnel_type, local_ip, remote_ip)
            tp = ovs_bridge.get_tunnel_port(tunnel_name, tunnel_type)
        except:
            raise

        output = { 'id': '%d' % id,
                   'tnrm': { 'tunnel': { 'name': '%s' % tp.port_name,
                                         'ofport': '%s' % tp.ofport,
                                         'type': '%s' % tp.tunnel_type,
                                         'local_ip': '%s' % tp.local_ip,
                                         'remote_ip': '%s' % tp.remote_ip }}}
        return output

    def tunnel_delete(self, dpid, params):
        ovsdb = params['tnrm']['ovsdb']
        tunnel_name = params['tnrm']['name']
        remote_ip = params['tnrm']['remote_ip']

        id = int(dpid, 16)

        try:
            self.del_port(ovsdb, dpid, tunnel_name)
        except:
            raise
            
        print "tunnel_name=%s" % tunnel_name
        print "tunnel_name=%s" % re.search(r'\d+', tunnel_name)

        output = { 'id': '%d' % id, 'tnrm': "" }
        return output

    def del_port(self, ovsdb, dpid, name):
        id = int(dpid, 16)
        ovs_bridge = bridge.OVSBridge(bridge.CONF, id, ovsdb)
        ovs_bridge.init()
        ovs_bridge.del_port(name)

class GreTnrmAPI(ControllerBase):
    def __init__(self, req, link, data, **config):
        print "GreTnrmAPI:__init__"
        super(GreTnrmAPI, self).__init__(req, link, data, **config)
        self.cntl = data['GreTnrmController']

    @route('router', '/ovsdb/{dpid}/ports', methods=['POST', 'GET'], 
           requirements={'dpid': DPID_PATTERN})
    def list_ports(self, req, dpid, **kwargs):
        print "GreTNrm:list_ports: dpid=%s" % dpid
        params = eval(req.body)
        output = self.cntl.list_ports(dpid, params)

        message = json.dumps(output)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)

    @route('router', '/ovsdb/{dpid}/tunnel/info', methods=['POST', 'GET'], 
           requirements={'dpid': DPID_PATTERN})
    def tunnel_info(self, req, dpid, **kwargs):
        print "GreTNrm:tunnel_info: dpid=%s" % dpid
        params = eval(req.body)
        output = self.cntl.tunnel_info(dpid, params)

        message = json.dumps(output)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)

    @route('router', '/ovsdb/{dpid}/tunnel/create', methods=['POST', 'GET'], 
           requirements={'dpid': DPID_PATTERN})
    def tunnel_create(self, req, dpid, **kwargs):
        print "GreTNrm:tunnel_create: dpid=%s" % dpid
        params = eval(req.body)
        output = self.cntl.tunnel_create(dpid, params)

        message = json.dumps(output)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)

    @route('router', '/ovsdb/{dpid}/tunnel/delete', methods=['POST', 'GET'], 
           requirements={'dpid': DPID_PATTERN})
    def tunnel_delete(self, req, dpid, **kwargs):
        print "GreTNrm:tunnel_delete: dpid=%s" % dpid
        params = eval(req.body)
        output = self.cntl.tunnel_delete(dpid, params)

        message = json.dumps(output)
        return Response(status=200,
                        content_type = 'application/json',
                        body = message)

