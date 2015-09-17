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
# from config import Config, Node, Interface
# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
# TNRM_CONFIG = 'config.xml'
# config = Config(TNRM_CONFIG)
# advertisement = config.get_advertisement()
# logger.debug("call get_advertisement, rspec=\n%s" % (advertisement))

from nsi2interface import *
from reservation import Request, Reservation, Manager, Endpoint, Path
nsi = NSI()

dict_resv = {}

#def get_advertisement():
#    logger.debug("call get_advertisement, rspec=\n%s" % (advertisement))
#    return advertisement

def reserve(gid, sstp, dstp, svlantag, dvlantag, bw, ep_start, ep_end):
    rid = nsi.reserve(gid, sstp, dstp, svlantag, dvlantag, bw, 
                      ep_start, ep_end, None)
    logger.debug("reservation ID=" + rid)
    if rid is None:
        raise Exception("proxy:reserve", "The reservatuin id is null.")
    return rid

def modify(gid, rid, ep_end):
    mid = nsi.modify(rid, rid, ep_end)
    logger.debug("reservation ID=" + rid + ", mid=" + mid)

    if mid is None:
        raise Exception("proxy:reserve", "The modification id  is null.")
    return mid

def provision(rid):
    nsi.provision(rid)
    return rid

def release(rid):
    nsi.release(rid)
    return rid

def terminate(rid):
    nsi.terminate(rid)
    return rid

server = SimpleXMLRPCServer(("localhost", 24444))
logger.debug("Listening on port 24444...")
# server.register_function(get_advertisement, "get_advertisement")
# server.register_function(get_manifest, "get_manifest")
# server.register_function(get_reservation, "get_reservation")
server.register_function(reserve, "reserve")
server.register_function(modify, "modify")
server.register_function(provision, "provision")
server.register_function(release, "release")
server.register_function(terminate, "terminate")
server.serve_forever()
