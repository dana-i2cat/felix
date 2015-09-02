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

import xmlrpclib

import tn_rm_exceptions as tnex
import log
logger = log.getLogger('tnrm:proxy')
logger.info("start proxy from TNRM to NSI.")

from SimpleXMLRPCServer import SimpleXMLRPCServer

from datetime import datetime, timedelta, time
from config import Config, Node, Interface, TNRM_Exception
# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
TNRM_CONFIG = 'config.xml'
config = Config(TNRM_CONFIG)
advertisement = config.get_advertisement()
logger.debug("call get_advertisement, rspec=\n%s" % (advertisement))

from nsi2interface import *
from reservation import Request, Reservation
nsi = NSI()

dict_resv = {}

def get_advertisement():
    logger.debug("call get_advertisement, rspec=\n%s" % (advertisement))
    return advertisement

def reserve(request, start_time, end_time):
    logger.debug("called reserve. rspec=\n%s" % (request))
    if request is None:
        raise tnex.RspecException("proxy:reserve", "The request rspec is null.")

    try:
        req = Request(request)
    except tnex.TnrmException:
        logger.error("new Request has error.")
        return None
    # if req is None:
    #     raise tnex.RspecException("proxy:reserve", "The request can not be parsed.");

    logger.debug("req=%s" % (req))
    resv = req.getReservation()
    logger.debug("reservation=%s" % (resv))

    logger.debug("start=%s" % (start_time))
    logger.debug("end=%s" % (end_time))
    resv.settime(start_time, end_time)

    logger.debug("reservation=%s" % (resv))
    rid = nsi.reserve(resv)
    logger.debug("reservation ID=" + rid)
    if dict_resv.has_key(rid):
        del dict_resv[rid]
    dict_resv[rid] = resv
    logger.debug("reservation add resv=%s" % (resv))
    return rid

def modify(rid, end_time):
    resv = dict_resv[rid]
    org_end_time = resv.end_time
    resv.settime(0, end_time)
    logger.debug("reservation=%s" % (resv))
    nsi.modify(rid, resv)
    return rid

def provision(rid):
    resv = dict_resv[rid]
    # if (isinstance(resv, type(None)) != True):
    # raise TNRM_Exception("no reserveation, id=." + rid)
        
    nsi.provision(rid)
    return rid

def release(rid):
    resv = dict_resv[rid]
    # if (isinstance(resv, type(None)) != True):
    # raise TNRM_Exception("no reserveation, id=." + rid)
        
    nsi.release(rid)
    return rid

def terminate(rid):
    resv = dict_resv[rid]
    # if (isinstance(resv, type(None)) != True):
    # raise TNRM_Exception("no reserveation, id=." + rid)
        
    nsi.terminate(rid)
    del dict_resv[rid]
    return rid

def get_manifest(rid):
    m = manifest_rspec_null
    logger.debug("manifest:rid=%s" % (rid))
    if rid is None:
        logger.debug("manifest:rspec=rid is None")
        return m

    logger.debug("manifest:#2rid=%s" % (rid))
    if dict_resv.has_key(rid):
        resv = dict_resv[rid]
        logger.debug("manifest:resv=%s" % (resv))
        m = resv.get_manifest()
    else:
        logger.debug("manifest:no entry")

    logger.debug("manifest:rid=%s" % (m))
    return m

manifest_rspec_null = """<?xml version="1.1" encoding="UTF-8"?>
<rspec type="manifest"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:stitch="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/
            http://hpn.east.isi.edu/rspec/ext/stitch/0.1/stitch-schema.xsd
            http://www.geni.net/resources/rspec/3/manifest.xsd
            http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">
    <!-- none -->
</rspec>
"""


server = SimpleXMLRPCServer(("localhost", 24444))
logger.debug("Listening on port 24444...")
server.register_function(get_advertisement, "get_advertisement")
server.register_function(get_manifest, "get_manifest")
#server.register_function(get_reservation, "get_reservation")
server.register_function(reserve, "reserve")
server.register_function(modify, "modify")
server.register_function(provision, "provision")
server.register_function(release, "release")
server.register_function(terminate, "terminate")
server.serve_forever()
