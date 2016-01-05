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
# logger = log.getLogger('tnrm:vlanManager')

# from tn_rm_delegate import logger
logger = log.getLogger('tnrm:vlanManager')
logger.info("vlanManager: ready")

dict_vlanManagers = {}
def get_vlanManager(stp):
    if dict_vlanManagers.has_key(stp):
        return dict_vlanManagers.has_key[stp]

    raise tnex.ParamException("vlanManagers:getVlanManager", "This stp (%s) does not exist." % (stp))

def get_vlanSet(vlans):
    dict_vlans = {}

    if vlans is not None:
        try:
            vv = vlans.split(",")
            for v in vv:
                vvv = v.split("-")
                if (len(vvv) == 2):
                    for i in range(int(vvv[0]), int(vvv[1])+1):
                        dict_vlans[str(i)] = i
                else:
                    s = v.strip()
                    dict_vlans[s] = int(s)

        except Exception as e:
            raise tnex.ParamException("vlanManager:", "This vlan parameter (%s) is bad format." % (vlans))

    return dict_vlans
                                 
def get_productSet(vlans1, vlans2):
    dict_product = {}

    if vlans1 is None or vlans2 is None:
        return dict_product
    if len(vlans1) == 0 or len(vlans2) == 0:
        return dict_product

    for v in vlans1.keys():
        if vlans2.has_key(v):
            dict_product[v] = int(v)

    return dict_product
    
def list_string(l):
    s = None
    min = 0
    max = 0
    for i in l:
        if min == 0:
            min = i 
            max = i
            continue
        
        if (max + 1) == i:
            max = i
            continue
        
        if max == min:
            if s is None:
                s = "%d" % (min)
            else:
                s = s + ",%d" % (min)
            min = i
            max = i
        else:
            if s is None:
                s = "%d-%d" % (min, max)
            else:
                s = s + ",%d-%d" % (min, max)
            min = i
            max = i

    if min != 0:
        if max == min:
            if s is None:
                s = "%d" % (min)
            else:
                s = s + ",%d" % (min)
        else:
            if s is None:
                s = "%d-%d" % (min, max)
            else:
                s = s + ",%d-%d" % (min, max)

    if s is None:
        s = ""
    return s

class vlanManager:
    def __init__(self, stp, vlans):
        self.stp = stp
        self.allowed_vlans = vlans
        self.dict_freed_green = {}
        self.dict_freed_yellow = {}
        self.dict_used = {}

        if vlans is None:
            vlans = "2-4094"

        self.dict_allowed = get_vlanSet(vlans)
                                 
        if stp is None:
            raise tnex.ParamException("vlanManager:init", "This stp is None.")
        if dict_vlanManagers.has_key(stp):
            raise tnex.ParamException("vlanManager:init", "This stp (%s) already exist." % (stp))

        dict_vlanManagers[stp] = self
        self.dict_freed_green = self.dict_allowed.copy()

        logger.debug("nsi stp: %s, vlans: %s" % (stp, vlans))

    def getVlan(self, vlans):
        dict_requested = get_vlanSet(vlans)
        list_requested = sorted(dict_requested.keys())

        logger.debug("freed:green: %d, yellow: %d, used: %d, allowed: %d" % 
                     (len(self.dict_freed_green), len(self.dict_freed_yellow),
                      len(self.dict_used), len(self.dict_allowed)))

        if len(self.dict_freed_green) == 0:
            if len(self.dict_freed_yellow) != 0:
                self.dict_freed_green = self.dict_freed_yellow.copy()
                self.dict_freed_yellow = {}

        for v in list_requested:
            if self.dict_freed_green.has_key(v):
                del self.dict_freed_green[v]
                self.dict_used[v] = int(v)
                return v

        for v in list_requested:
            if self.dict_freed_yellow.has_key(v):
                del self.dict_freed_yellow[v]
                self.dict_used[v] = int(v)
                return v

        raise tnex.ParamException("vlanManager:getVlan", "This vlan (%s) is not freed." % (vlans))

    def checkVlan(self, vlan):
        if self.dict_allowed.has_key(vlan):
            return True

        logger.info("checkVlans: False")
        raise tnex.ParamException("vlanManager:checkVlan", "This vlan (%s) is not allowed." % (vlan))

    def productAllowedVlans(self, vlans):
        # logger.info("productAllowedVlans: vlans=%s" % vlans)
        dict_requested = get_vlanSet(vlans)
        # logger.info("productAllowedVlans: requested=%s" % dict_requested)
        
        dict_product = get_productSet(dict_requested, self.dict_allowed)
        # logger.info("productAllowedVlans: result=%s" % dict_product)
        return dict_product

    def putVlanYellow(self, vlan):
        try:
            self.checkVlan(vlan)
        except Exception as e:
            logger.warning("vlanManager:putVlanYellow", "This vlan (%s) is not allowed." % (vlan))
            return None
            
        if self.dict_used.has_key(vlan):
            del self.dict_used[vlan]
            self.dict_freed_yellow[vlan] = int(vlan)
            return vlan
        else:
            logger.warning("vlanManager:putVlanYellow", "This vlan (%s) is not used." % (vlan))
        return None
        
    def putVlan(self, vlan):
        try:
            self.checkVlan(vlan)
        except Exveption as e:
            logger.warning("vlanManager:putVlan", "This vlan (%s) is not allowed." % (vlan))
            return None
            
        if self.dict_used.has_key(vlan):
            del self.dict_used[vlan]
            self.dict_freed_green[vlan] = int(vlan)
            return vlan
        else:
            logger.warning("vlanManager:putVlan", "This vlan (%s) is not used." % (vlan))
        return None
        
    def getFreeList(self):
        list_green = self.dict_freed_green.values()
        list_yellow = self.dict_freed_yellow.values()
        list_free = list_green + list_yellow

        list_sort = sorted(list_free)
        s = list_string(list_sort)
        return s

    def getUsedList(self):
        list_used = self.dict_used.values()

        list_sort = sorted(list_used)
        s = list_string(list_sort)
        return s

    def __str__(self):
        s = "stp=%s: allowed=%s, freed=%s, used=%s" % (self.stp, self.allowed_vlans, self.getFreeList(), self.getUsedList())
        return s

if __name__ == "__main__":
    vrange = "100, 1779-1799, 2000, 2779-2799, 3000"
    vman = VlanManager ("stp-1", vrange)
    print vman
    v = vman.getVlan("2000")
    print "get=%s " % v

    v = vman.getVlan("1790")
    print "get=%s " % v

    v = vman.getVlan("100-200,2791-2795")
    print "get=%s " % v

    v = vman.getVlan("100-200,2791-2795")
    print "get=%s " % v

    v = vman.getVlan("100-200,2791-2795")
    print "get=%s " % v

    v = vman.putVlan("2792")
    print "put=%s " % v

    try:
        v = vman.putVlan("2750")
        print "put=%s " % v
    except Exception as e:
        print "**************"
        print e
        print "**************"
        
    v = vman.getVlan("100-200,3000")
    print "get=%s " % v

    print vman

    try:
        vrange = "1779-1799"
        vman = VlanManager ("stp-1", vrange)
    except Exception as e:
        print "**************"
        print e
        print "**************"

    vrange = "1779-1799"
    vman = VlanManager ("stp-2", vrange)
    for i in range(1779, 1800):
        v = vman.getVlan(vrange)
        print "get=%s " % v
        vman.putVlanYellow(v)


    try:
        v = vman.getVlan("1790")
        print "get=%s " % v
        v = vman.putVlan("1790")
    except Exception as e:
        print "**************"
        print e
        print "**************"

    print "*************************"
    for i in range(1779, 1800):
        v = vman.getVlan(vrange)
        print "get=%s " % v

    try:
        v = vman.getVlan("1790")
        print "get=%s " % v
    except Exception as e:
        print "**************"
        print e
        print "**************"

    allows =vman.productAllowedVlans("1795-3000")
    print allows

    v = vman.putVlan("1790")
    v = vman.putVlan("1791")
    v = vman.putVlan("1793")
    v = vman.putVlan("1788")
    print vman.getFreeList()

    print vman
