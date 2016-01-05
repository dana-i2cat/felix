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

# import amsoil.core.log
# logger = amsoil.core.log.getLogger('TN-RM:ovsgre')
# import log
# logger = log.getLogger('tnrm:ovsgre')
from tn_rm_delegate import logger
logger.info("start proxy from TNRM to OVSGRE.")

from tn_rm_exceptions import ManagerException, ParamException
from datetime import datetime, timedelta, time
from reservation import Request, Reservation, Manager, Endpoint, Path
from proxy_interface import Proxy
import ovsif as ovsif

import uuid

dict_ovsManager = {}
dict_resvParameter = {}
dict_vlanManager = {}
dict_swManager = {}
tvlan_min = 1500
tvlan_max = 3000

dev_min = 1
dev_max = 999

bond = "/"

OF_PRIORITY = 1000
OF_TIMEOUT = 0
OF_COOKIE = 1
OF_COOKIE_MASK = 1
OF_TABLE_ID = 0
OF_FLAGS = 1

def getKey (s_stp, d_stp):
    key = s_stp + bond + d_stp
    return key

def get_swManager (interface):
    stp = interface.nsi_stp_id
    key = interface.ryu_url + "/" + interface.dpid
    logger.info("get_swManager: key=%s" % key)

    if dict_swManager.has_key(key):
        return dict_swManager[key]

    logger.info("get_swManager: new swManager")
    sw = swManager(interface)
    dict_swManager[key] = sw
    return sw

def get_ovsManagerKey (src_if, dst_if):
    key = src_if.nsi_stp_id + bond + dst_if.nsi_stp_id
    return key

def get_ovsManager (src_if, dst_if):
    key = get_ovsManagerKey (src_if, dst_if)
    logger.info("get_ovsManager: %s" % key)

    if dict_ovsManager.has_key(key):
        logger.info("get_ovsManager: %s is already exist." % key)
        return dict_ovsManager[key]

    key = get_ovsManagerKey (dst_if, src_if)
    if dict_ovsManager.has_key(key):
        logger.info("get_ovsManager: %s is already exist." % key)
        return dict_ovsManager[key]

    key = get_ovsManagerKey (src_if, dst_if)
    ovsManager = OvsManager(src_if, dst_if)
    logger.info("get_ovsManager: %s is created now." % key)
    dict_ovsManager[key] = ovsManager
    return dict_ovsManager[key]

def get_vlanManager (s_stp, d_stp):
    if s_stp is None:
        raise ManagerException("ovsgre:get_vlanMamager", "The source stp is None.")
    if d_stp is None:
        raise ManagerException("ovsgre:get_vlanMamager", "The destination stp is None.")

    key = getKey(s_stp, d_stp)
    if dict_vlanManager.has_key(key):
        if not dict_vlanManager.has_key(s_stp):
            raise ManagerException("Never here. This is a fatal error to manage vlanManager. stp=%s" % (s_stp))
        if not dict_vlanManager.has_key(d_stp):
            raise ManagerException("Never here. This is a fatal error to manage vlanManager. stp=%s" % (d_stp))
        return (dict_vlanManager[s_stp], dict_vlanManager[d_stp], dict_vlanManager[key])

    key = getKey(d_stp, s_stp)
    if dict_vlanManager.has_key(key):
        if not dict_vlanManager.has_key(d_stp):
            raise ManagerException("Never here. This is a fatal error to manage vlanManager. stp=%s" % (d_stp))
        if not dict_vlanManager.has_key(s_stp):
            raise ManagerException("Never here. This is a fatal error to manage vlanManager. stp=%s" % (s_stp))
        return (dict_vlanManager[d_stp], dict_vlanManager[s_stp], dict_vlanManager[key])

    key = getKey(s_stp, d_stp)
    dict_vlanManager[key] = vlanManager(key, True)
    if not dict_vlanManager.has_key(s_stp):
        dict_vlanManager[s_stp] = vlanManager(s_stp)
    if not dict_vlanManager.has_key(d_stp):
        dict_vlanManager[d_stp] = vlanManager(d_stp)

    return  (dict_vlanManager[s_stp], dict_vlanManager[d_stp], dict_vlanManager[key])

class vlanManager:
    def __init__ (self, stp, isTunnel = False):
        self.stp = stp
        self.isTunnel = isTunnel
        self.dict_vlans = {}
        self.vlan_min = -1
        self.vlan_max = -1
        self.vlan_pos = -1

        if self.isTunnel:
            self.vlan_min = tvlan_min
            self.vlan_max = tvlan_max
            self.vlan_pos = self.vlan_min

    def search (self):
        for v in xrange(self.vlan_pos, self.vlan_max):
            logger.info("ovsgre:vlanManager:search: vlan=%d" % (v))
            if self.dict_vlans.has_key(str(v)):
                continue
            else:
                self.vlan_pos = v + 1
                if self.vlan_pos == self.vlan_max:
                    self.vlan_pos = self.vlan_min
                return str(v)
                
        for v in xrange(self.vlan_min, self.vlan_pos):
            logger.info("ovsgre:vlanManager:search: vlan=%d" % (v))
            if self.dict_vlans.has_key(str(v)):
                continue
            else:
                self.vlan_pos = v + 1
                if self.vlan_pos == self.vlan_max:
                    self.vlan_pos = self.vlan_min
                return str(v)

        raise ManagerException("proxy:allocate_vlan", "New vlan is not allocated.")

    def allocate (self, vlan = None):
        logger.info("ovsgre:vlanManager:allocate: vlan=%s" % (vlan))
        ivlan = 0
        if vlan is not None:
            try:
                ivlan = int(vlan)
            except Exception:
                raise ManagerException("ovsgre:allocate", "This vlan (%s) can not convert to integer." % vlan)

            # if (ivlan < self.vlan_min or ivlan > self.vlan_max):
            #   raise ManagerException("ovsgre:allocate", "This vlan (%s) is outof vlan range." % vlan)

        if vlan is None:
            if self.isTunnel:
                vlan = self.search()
                logger.info("VlanManagter: new allocate vlan is %s." % (vlan))
            else:
                raise ManagerException("ovsgre:allocate", "Vlan is unset for STP.")

        if self.dict_vlans.has_key(vlan):
            raise ManagerException("ovsgre:allocate", "This vlan (%s) is already used." % vlan)

        self.dict_vlans[vlan] = vlan
        return vlan

    def free (self, vlan):
        if self.dict_vlans.has_key(vlan):
            del self.dict_vlans[vlan]
        return vlan

class resvParameter:
    def __init__ (self, ovs_id, resv):
        self.ovs_id = ovs_id;
        self.resv = resv;
        self.s_stp = self.resv.path.sep.stp
        self.d_stp = self.resv.path.dep.stp
        self.t_stp = getKey(self.s_stp, self.d_stp)

        #self.s_vlan = self.resv.path.sep.vlantag
        #self.d_vlan = self.resv.path.dep.vlantag
        self.s_vlan = self.resv.src_vlan
        self.d_vlan = self.resv.dst_vlan
        self.t_vlan = self.resv.trans_vlan
        self.s_if = self.resv.src_if
        self.d_if = self.resv.dst_if

        self.s_vman = None
        self.d_vman = None
        self.t_vman = None
        (self.s_vman, self.d_vman, self.t_vman) = get_vlanManager(self.s_stp, self.d_stp)
        
        self.s_ofdev, self.s_ofport = self.s_if.get_of(self.ovs_id)
        self.d_ofdev, self.d_ofport = self.d_if.get_of(self.ovs_id)
        logger.info("ovsgre:ResvParameter:init: %s" % self)

    def __str__(self):
        self.s_ofdev, self.s_ofport = self.s_if.get_of(self.ovs_id)
        self.d_ofdev, self.d_ofport = self.d_if.get_of(self.ovs_id)
        return "s_stp=%s/%s/%s, d_stp=%s/%s/%s" %(self.s_stp, self.s_vlan, self.s_ofdev, self.d_stp, self.d_vlan, self.d_ofdev)

    def allocate (self):
        try:
            self.s_vman.allocate(self.s_vlan)
        except Exception as ex:
            raise ex

        try:
            self.d_vman.allocate(self.d_vlan)
        except Exception as ex:
            self.s_vman.free(self.s_vlan)
            raise ex

        try:
            self.t_vlan = self.t_vman.allocate(self.t_vlan)
        except Exception as ex:
            self.s_vman.free(self.s_vlan)
            self.d_vman.free(self.d_vlan)
            raise ex

        logger.info("allocated vlan src:%s, dst:%s, tun:%s" % (self.s_vlan, self.d_vlan, self.t_vlan))
        return (self.s_vlan, self.d_vlan, self.t_vlan)
    
    def free (self):
        keep = None
        try:
            self.s_vman.free(self.s_vlan)
        except Exception as ex:
            logger.info("free: source vlan tun:%s" % (self.s_vlan))
            keep = ex

        try:
            self.d_vman.free(self.d_vlan)
        except Exception as ex:
            logger.info("destination vlan tun:%s" % (self.d_vlan))
            keep = ex

        try:
            self.t_vman.free(self.t_vlan)
        except Exception as ex:
            logger.info("tunnel vlan tun:%s" % (self.t_vlan))
            keep = ex

        if keep is not None:
            raise keep

        logger.info("freed vlan src:%s, dst:%s, tun:%s" % (self.s_vlan, self.d_vlan, self.t_vlan))
        return (self.s_vlan, self.d_vlan, self.t_vlan)

class swManager:
    def __init__ (self, src_if):
        self.src_if = src_if
        self.dict_dev = {}
        self.dict_path = {}
        self.key = self.src_if.ryu_url + "/" + self.src_if.dpid
        logger.info("swManager: init: key=%s." % self.key)

    def set_used(self, dev, ofport):
        self.dict_dev[dev] = ofport
        logger.info("swManager: set_used: dev=%s, ofport=%s." % (dev, ofport))

    def set_free(self, dev):
        del self.dict_dev[dev]
        logger.info("swManager: set_free: dev=%s." % dev)

    def get_port(self, dev):
        if self.dict_dev.has_key(dev):
            port = self.dict_dev[dev]
            logger.info("swManager: get_port: dev=%s, ofport=%s" % (dev, port))
            return self.dict_dev[dev]

        raise ManagerException("ovsgre:swManager:get_port", "This dev(%s) does not exist." % dev)

    def allocate_dev(self, dst_if):
        lkey = self.key + ":" + dst_if.ryu_url + "/" + dst_if.dpid
        logger.info("swManager:allocate_dev: lkey=%s." % lkey)

        if self.dict_path.has_key(lkey):
            dev = self.dict_key[lkey]
            logger.info("swManager:allocate_dev: old device is %s." % dev)
            # return self.dict_dev[lkey]
            return dev

        for v in xrange(dev_min, dev_max):
            dev = "%s%03d" % (ovsif.PREFIX_DEV, v)
            if dev in self.dict_dev:
                continue
            else:
                logger.info("swManager:allocate_dev: new device is %s." % dev)
                self.dict_path[lkey] = dev
                self.set_used(dev, None)
                return dev

        raise ManagerException("OvsManager:swManager:allocate_dev", 
                               "There is no resources for device in openvSwitch.")
            
class OvsManager:
    def __init__ (self, src_if, dst_if):
        self.ovs_id = get_ovsManagerKey(src_if, dst_if)
        self.src_if = src_if
        self.dst_if = dst_if
        self.isSetup = False
        self.dict_used = {}
        self.dict_isSetRule = {}
        self.src_swManager = get_swManager(self.src_if)
        self.dst_swManager = get_swManager(self.dst_if)

        self.src_if.seport = self.get_port(self.src_if)
        self.dst_if.seport = self.get_port(self.dst_if)

        (ofdev, ofport) = self.find_dev(self.src_if, self.dst_if)
        self.src_if.set_of(self.ovs_id, ofdev, ofport)
        # self.src_if.ofdev = ofdev
        # self.src_if.ofport = ofport
        if ofdev is not None:
            self.src_swManager.set_used(ofdev, ofport)
        else:
            ofdev = self.src_swManager.allocate_dev(self.dst_if)
            self.src_if.set_of(self.ovs_id, ofdev, None)
            self.src_swManager.set_used(ofdev, None)

        (ofdev, ofport) = self.find_dev(self.dst_if, self.src_if)
        self.dst_if.set_of(self.ovs_id, ofdev, ofport)
        # self.dst_if.ofdev = ofdev
        # self.dst_if.ofport = ofport
        if ofdev is not None:
            self.dst_swManager.set_used(ofdev, ofport)
        else:
            ofdev = self.dst_swManager.allocate_dev(self.src_if)
            self.dst_if.set_of(self.ovs_id, ofdev, None)
            self.dst_swManager.set_used(ofdev, None)

    def get_port(self, interface):
        urlbase = interface.ryu_url
        dpid = interface.dpid

        params = {}
        params["ovsdb"] = interface.ovsdb
        name = interface.sedev

        port = ovsif.get_port(urlbase, dpid, params, name)
        logger.info("get port. url=%s, dpid=%s, ovsdb=%s, dev=%s" % (urlbase, dpid, params["ovsdb"], name))
        return port

    def find_dev(self, src_if, dst_if):
        urlbase = src_if.ryu_url
        dpid = src_if.dpid

        params = {}
        params["ovsdb"] = src_if.ovsdb
        if (src_if.gtype == "ovsgre"):
            params["type"] = "gre"
        else:
            raise ManagerException("OvsManager:find_dev", 
                                   "Type (%s) is unknown, must be \"ovsgre\"." % (src_if.gtype))
        params["local_ip"] = src_if.address
        params["remote_ip"] = dst_if.address

        logger.info("search gre link. url=%s, dpid=%s, ovsdb=%s, type=%s, local=%s, remote=%s" % (urlbase, dpid, params["ovsdb"], params["type"], params["local_ip"], params["remote_ip"]));

        finds = ovsif.get_tunnel_info(urlbase, dpid, params)
        if len(finds) == 0:
            return (None, None)
        elif len(finds) == 1:
            for p in finds.keys():
                logger.info("find gre link. dev=%s, ofport=%s" % (p, finds[p]))
                return (p, finds[p])
        else:
            raise ManagerException("OvsManager:init", "Duplicate path is exist. %s" % finds)

    def check_stp (self, resv):
        if resv.src_if == self.src_if and resv.dst_if == self.dst_if:
            return True
        if resv.src_if == self.dst_if and resv.dst_if == self.src_if:
            return True

        raise ManagerException("ovs manager:check_stp", "Mismatch interface between OvsManager and Reservation. %s:%s, %s:%s" % (self.src_if, self.dst_if, resv.src_if, resv.dst_if))

    def reserve (self, resv):
        # logger.info("ovsgre:OvsManager:reserve: enter")
        # This just only reserve vlans for source/destination/tunnel interfaces
        if resv is None:
            raise ManagerException("OvsManager:reserve", "The reservation parameter is null.")
        
        self.check_stp(resv)

        resv_id = uuid.uuid4()
        logger.info("ovsManager:reserve: new resv_id=%s." % resv_id)
        
        if dict_resvParameter.has_key(resv_id):
            logger.error("Never here. Reservation id is duplicated(%s)." % (resv_id))
            raise ManagerException("OvsManager:reserve", "The reservation id is already used.")

        resvp = resvParameter(self.ovs_id, resv)

        (s_vlan, d_vlan, t_vlan) = resvp.allocate()
        resv.trans_vlan = t_vlan

        dict_resvParameter[resv_id] = resvp
        self.dict_isSetRule[resv_id] = False
        logger.info("ovsManager:reserve: done. resv_id=%s" % (resv_id))
        return resv_id

    def modify (self, resv, end_time_sec):
        # This do nothing here.
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            raise ManagerException("OvsManager:modify", "The reservation is null.")
        return resv.resv_id

    def setup_tunnel(self, src_if, dst_if):
        logger.info("setup src_if=%s" % src_if)
        logger.info("setup dst_if=%s" % dst_if)

        sw = get_swManager(src_if)
        ofport = None

        try:
            # ofport = sw.get_port(src_if.ofdev)
            ofdev, ofport = src_if.get_of(self.ovs_id)
            ofport2 = sw.get_port(ofdev)
            if ofport != ofport2:
                logger.error("setup_tunnel:ofdev=%s: mismatch ofport=%s, ofport2=%s" % (ofdev, ofport, ofport2))
                ofport = ofport2
        except Exception as ex:
            logger.info("setup_tunnel:gre port is None")
            
        if ofport is None:
            urlbase = src_if.ryu_url
            dpid = src_if.dpid

            logger.info("setup gre link here. url=%s, dpid=%s, ovsdb=%s, dev=%s, type=%s, local=%s, remote=%s" %
                        (urlbase, dpid, src_if.ovsdb, ofdev, src_if.gtype, src_if.address, dst_if.address));

            params = {}
            params["ovsdb"] = src_if.ovsdb
            params["name"] = ofdev
            if (src_if.gtype == "ovsgre"):
                params["type"] = "gre"
            else:
                raise ManagerException("OvsManager:setup_tunnel", 
                                       "Type (%s) is unknown, must be \"ovsgre\"." % (src_if.gtype))
            params["local_ip"] = src_if.address
            params["remote_ip"] = dst_if.address

            ofport = ovsif.add_tunnel(urlbase, dpid, params)

        # src_if.ofport = ofport
        src_if.set_of(self.ovs_id, ofdev, ofport)
        sw.set_used(ofdev, ofport)

    def teardown_tunnel(self, src_if, dst_if):
        sw = get_swManager(src_if)
        ofport = None
        
        try:
            # ofport = sw.get_port(src_if.ofdev)
            ofdev, ofport = src_if.get_of(self.ovs_id)
            ofport2 = sw.get_port(ofdev)
            if ofport != ofport2:
                logger.error("teardown_tunnel:ofdev=%s: mismatch ofport=%s, ofport2=%s" % (ofdev, ofport, ofport2))
                ofport = ofport2
        except Exception as e:
            logger.info("teardown_tunnel:gre port is None")
            
        if ofport is not None:
            urlbase = src_if.ryu_url
            dpid = src_if.dpid

            logger.info("teardown gre link here. url=%s, dpid=%s, ovsdb=%s, dev=%s, type=%s, local=%s, remote=%s" %
                        (urlbase, dpid, src_if.ovsdb, ofdev, src_if.gtype, src_if.address, dst_if.address));

            params = {}
            params["ovsdb"] = src_if.ovsdb
            params["name"] = ofdev
            params["remote_ip"] = dst_if.address

            ovsif.del_tunnel(urlbase, dpid, params)

        # src_if.ofport = None
        src_if.set_of(self.ovs_id, ofdev, None)
        sw.set_free(ofdev)

    def add_rule(self, interface, sevlan, ofvlan):
        urlbase = interface.ryu_url
        dpid = interface.dpid
        ofdev, ofport = interface.get_of(self.ovs_id)

        params = {}
        params["dpid"] = int(dpid, 16)
        params["priority"] = OF_PRIORITY
        params["idel_timeout"] = OF_TIMEOUT
        params["hard_timeout"] = OF_TIMEOUT
        params["cookie"] = OF_COOKIE
        params["cookie_mask"] = OF_COOKIE_MASK
        params["table_id"] = OF_TABLE_ID
        params["flags"] = OF_FLAGS

        matchs = {"in_port": interface.seport, "dl_vlan": sevlan} 
        params["match"] = matchs
        # actions = [{"type":"SET_VLAN_VID", "vlan_vid": ofvlan}, {"type":"OUTPUT", "port": interface.ofport}] 
        actions = [{"type":"SET_VLAN_VID", "vlan_vid": ofvlan}, {"type":"OUTPUT", "port": ofport}] 
        params["actions"] = actions
        rc = ovsif.add_flow(urlbase, params)
        logger.info("add_rule: ret=%s" % rc)

        # matchs = {"in_port": interface.ofport, "dl_vlan": ofvlan} 
        matchs = {"in_port": ofport, "dl_vlan": ofvlan} 
        params["match"] = matchs
        actions = [{"type":"SET_VLAN_VID", "vlan_vid": sevlan}, {"type":"OUTPUT", "port": interface.seport}] 
        params["actions"] = actions
        rc = ovsif.add_flow(urlbase, params)
        logger.info("add_rule: ret=%s" % rc)

    def del_rule(self, interface, sevlan, ofvlan):
        urlbase = interface.ryu_url
        dpid = interface.dpid
        ofdev, ofport = interface.get_of(self.ovs_id)

        params = {}
        params["dpid"] = int(dpid, 16)

        matchs = {"in_port": interface.seport, "dl_vlan": sevlan} 
        params["match"] = matchs
        rc = ovsif.del_flow(urlbase, params)
        logger.info("del_rule: ret=%s" % rc)

        # matchs = {"in_port": interface.ofport, "dl_vlan": ofvlan} 
        matchs = {"in_port": ofport, "dl_vlan": ofvlan} 
        params["match"] = matchs
        rc = ovsif.del_flow(urlbase, params)
        logger.info("del_rule: ret=%s" % rc)

    def check_rule(self, interface, sevlan, ofvlan):
        urlbase = interface.ryu_url
        dpid = interface.dpid
        ofdev, ofport = interface.get_of(self.ovs_id)

        params = {}
        params["dpid"] = int(dpid, 16)

        matchs = {"in_port": interface.seport, "dl_vlan": sevlan} 
        params["match"] = matchs

        rc = ovsif.check_flows(urlbase, params, interface.seport, sevlan)
        if not rc:
            return False

        # matchs = {"in_port": interface.ofport, "dl_vlan": ofvlan} 
        matchs = {"in_port": ofport, "dl_vlan": ofvlan} 
        params["match"] = matchs
        rc1 = ovsif.check_flows(urlbase, params, ofport, ofvlan)
        if not rc1:
            return False

        return True

    def re_provision (self, resv):
        # provison:nsiv2, poa geni_start
        logger.info("ovsManager:re_provision has_key(%s)=%s" %
                    (resv.resv_id, dict_resvParameter.has_key(resv.resv_id)))
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            logger.info("ovsManager:re_provision: resv_id=%s" % (resv.resv_id))
            for key in dict_resvParameter:
                logger.info("ovsManager:re_provision: resvp=%s" % (key))
            raise ManagerException("OvsManager:re_provision", "The reservation is null.")

        resvp = dict_resvParameter[resv.resv_id]
        if resvp is None:
            raise ManagerException("OvsManager:re_privision", "The ResvParameter is null.")

        self.isSetup = True
        self.dict_used[resv.resv_id] = resv.resv_id
        self.dict_isSetRule[resv.resv_id] = True

        logger.info("ovsManager:re_provision: done. resv_id=%s" % (resv.resv_id))
        return resv.resv_id

    def provision (self, resv):
        # provison:nsiv2, poa geni_start
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            logger.info("ovsManager:provision: resv_id=%s" % (resv.resv_id))
            for key in dict_resvParameter:
                logger.info("ovsManager:provision: resvp=%s" % (key))
            raise ManagerException("OvsManager:provision", "The reservation is null.")
        
        resvp = dict_resvParameter[resv.resv_id]
        if resvp is None:
            raise ManagerException("OvsManager:privision", "The ResvParameter is null.")

        if self.isSetup:
            # already setup
            pass
        else:
            try:
                ### setup src->dst
                self.setup_tunnel(self.src_if, self.dst_if)
            except:
                raise

            try:
                ### setup dst->src
                self.setup_tunnel(self.dst_if, self.src_if)
            except:
                ### teardown tunnel by setup_tunnel(self.src_if, self.dst_if)
                self.teardown_tunnel(self.src_if, self.dst_if)
                raise
                
            self.isSetup = True

        self.dict_used[resv.resv_id] = resv.resv_id

        if self.dict_isSetRule[resv.resv_id]:
            # already set flow rule
            pass
        else:
            #### add code for set rule
            logger.info("set flow rule. %s?vlan=%s:%s?vlan=%s, gre?vlan=%s." % 
                        (resvp.s_stp, resvp.s_vlan, resvp.d_stp, resvp.d_vlan, resvp.t_vlan))
            try:
                ### add src
                self.add_rule(self.src_if, resvp.s_vlan, resvp.t_vlan)
            except Exception as ex:
                logger.error("provision: error in add rule: src_if=%s sevlan=%s, ofvlan=%s, ex=%s" % (self.src_if, resvp.s_vlan, resvp.t_vlan, ex))
                raise ex

            try:
                ### add dst
                self.add_rule(self.dst_if, resvp.d_vlan, resvp.t_vlan)
            except Exception as ex:
                logger.error("provision: error in add rule: dst_if=%s sevlan=%s, ofvlan=%s, ex=%s" % (self.dst_if, resvp.s_vlan, resvp.t_vlan, ex))
                self.del_rule(self.src_if, resvp.s_vlan, resvp.t_vlan)
                raise ex

            self.dict_isSetRule[resv.resv_id] = True

        return resv.resv_id

    def release (self, resv):
        e = None
        ### release:nsiv2, poa geni_stop
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            raise ManagerException("OvsManager:release", "The reservation is null.")
        
        resvp = dict_resvParameter[resv.resv_id]
        if resvp is None:
            raise ManagerException("OvsManager:release", "The ResvParameter is null.")

        if self.dict_isSetRule.has_key(resv.resv_id):
            if self.dict_isSetRule[resv.resv_id]:
                logger.info("delete flow rule here. %s?vlan=%s:%s?vlan=%s, gre?vlan=%s." % 
                            (resvp.s_stp, resvp.s_vlan, resvp.d_stp, resvp.d_vlan, resvp.t_vlan))

                try:
                    ### delete src
                    self.del_rule(self.src_if, resvp.s_vlan, resvp.t_vlan)
                except Exception as ex:
                    e = ex
                    logger.error("release: error in delete rule: src_if=%s sevlan=%s, ofvlan=%s, ex=%s" % (self.src_if, resvp.s_vlan, resvp.t_vlan, ex))

                try:
                    ### delete dst
                    self.del_rule(self.dst_if, resvp.d_vlan, resvp.t_vlan)
                except Exception as ex:
                    e = ex
                    logger.error("release: error in delete rule: dst_if=%s sevlan=%s, ofvlan=%s, ex=%s" % (self.dst_if, resvp.d_vlan, resvp.t_vlan, ex))

                self.dict_isSetRule[resv.resv_id] = False
                
            else:
                # already delete flow rule
                pass

        else:
            logger.info("OvsManager:release: This reservation (%s) does not have isSetRule." %
                        (resv.resv_id))

        if self.dict_used.has_key(resv.resv_id):
            del self.dict_used[resv.resv_id]
        else:
            logger.info("OvsManager:release: This reservation (%s) does not used this gre link." %
                        (resv.resv_id))

        if self.isSetup:
            if len(self.dict_used) > 0:
                logger.info("This gre link is shared other reservtion. Do not teardown now.")
            else:
                e = None
                ### teardown src->dst
                try:
                    self.teardown_tunnel(self.src_if, self.dst_if)
                except Exception as ex:
                    e = ex
                    logger.error("release: error in teardown: src_if=%s, dst_if=%s ex=%s" % (self.src_if, self.dst_if, ex))

                ### teardown dst->src
                try:
                    self.teardown_tunnel(self.dst_if, self.src_if)
                except Exception as ex:
                    e = ex
                    logger.error("release: error in teardown: src_if=%s, dst_if=%s ex=%s" % (self.dst_if, self.src_if, ex))

                self.isSetup = False
                self.isSetup = False

        else:
            logger.info("This link is already teardown.");
            
        if e is not None:
            raise e

        return resv.resv_id

    def terminate (self, resv):
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            raise ManagerException("OvsManager:terminate", "The reservation is null.")

        resvp = dict_resvParameter[resv.resv_id]
        if resvp is None:
            raise ManagerException("OvsManager:terminate", "The ResvParameter is null.")

        self.release(resv)

        resvp.free()
        del dict_resvParameter[resv.resv_id]

        if self.dict_used.has_key(resv.resv_id):
            del self.dict_used[resv.resv_id]
        if self.dict_isSetRule.has_key(resv.resv_id):
            del self.dict_isSetRule[resv.resv_id]

        return resv.resv_id

    def status (self, resv):
        if resv is None or not dict_resvParameter.has_key(resv.resv_id):
            logger.info("ovsManager:status: resv_id=%s" % (resv.resv_id))
            for key in dict_resvParameter:
                logger.info("ovsManager:status: resvp=%s" % (key))
            raise ManagerException("OvsManager:status", "The reservation is null.")

        resvp = dict_resvParameter[resv.resv_id]
        if resvp is None:
            raise ManagerException("OvsManager:status", "The ResvParameter is null.")

        rc = self.check_rule(self.src_if, resvp.s_vlan, resvp.t_vlan)
        if not rc:
            ### This operation is caused we can not remove flow rules 
            ### and teardown gre tunnel in a normal island.
            # self.dict_isSetRule[resv.resv_id] = False
            return False

        rc = self.check_rule(self.dst_if, resvp.d_vlan, resvp.t_vlan)
        if not rc:
            ### This operation is caused we can not remove flow rules 
            ### and teardown gre tunnel in a normal island.
            # self.dict_isSetRule[resv.resv_id] = False
            return False
        return True

    def swap_id (self, resv, new_id, old_id):
        if resv is None:
            raise ManagerException("OvsManager:swap_id", "The reservation is null.")
        if not dict_resvParameter.has_key(resv.resv_id):
            resvp = dict_resvParameter[new_id]
            del dict_resvParameter[new_id]
            dict_resvParameter[old_id] = resvp

        return resv.resv_id

class ovs_proxy (Proxy):
    def reserve (self, resv):
        # logger.info("ovsgre:ovs_proxy:reserve: enter")
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.reserve(resv)
        return resv_id

    def modify (self, resv, end_time_sec):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.modify(resv, end_time_sec)
        return resv_id

    def provision (self, resv):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.provision(resv)
        return resv_id

    def re_provision (self, resv):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.re_provision(resv)
        return resv_id

    def release (self, resv):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.release(resv)
        return resv_id

    def terminate (self, resv):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.terminate(resv)
        return resv_id

    def status (self, resv):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.status(resv)
        return resv_id

    def swap_id(self, resv, new_id, old_id):
        ovsManager = get_ovsManager(resv.src_if, resv.dst_if)
        resv_id = ovsManager.swap_id(resv, new_id, old_id)
        return resv_id

