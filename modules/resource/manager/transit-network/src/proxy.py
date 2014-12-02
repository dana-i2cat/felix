import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

from datetime import datetime, timedelta, time
from config import Config, Node, Interface, TNRM_Exception
# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
TNRM_CONFIG = 'config.xml'
config = Config(TNRM_CONFIG)
advertisement = config.get_advertisement()

from nsi2interface import *
from reservation import Request, Reservation
nsi = NSI()

dict_resv = {}

def get_advertisement():
    print "call get_advertisement"
    # print advertisement
    return advertisement

def reserve(request, start_time, end_time):
    print "call get_reservation"
    # print request
    req = Request(request)
    # print "req=%s" % (req)
    resv = req.getReservation()
    print "start=%s" % (start_time)
    print "end=%s" % (end_time)

    resv.settime(start_time, end_time)
    print "reservation=%s" % (resv)
    rid = nsi.reserve(resv)
    print "reservation ID=" + rid
    dict_resv[rid] = resv
    return rid

def modify(rid, end_time):
    resv = dict_resv[rid]
    org_end_time = resv.end_time
    resv.settime(0, end_time)
    print "reservation=%s" % (resv)
    nsi.modify(rid, resv)
    return rid

def provision(rid):
    resv = dict_resv[rid]
    # if (isinstance(resv, type(None)) != True):
    # raise TNRM_Exception("no reserveation, id=." + rid)
        
    nsi.provision(rid)
    return rid

def terminate(rid):
    resv = dict_resv[rid]
    # if (isinstance(resv, type(None)) != True):
    # raise TNRM_Exception("no reserveation, id=." + rid)
        
    nsi.terminate(rid)
    del dict_resv[rid]
    return rid

def get_manifest(rid):
    resv = dict_resv[rid]
    if (isinstance(resv, type(None)) != True):
        return resv.get_manifest()
    else:
        return ""

server = SimpleXMLRPCServer(("localhost", 24444))
print "Listening on port 24444..."
server.register_function(get_advertisement, "get_advertisement")
server.register_function(get_manifest, "get_manifest")
#server.register_function(get_reservation, "get_reservation")
server.register_function(reserve, "reserve")
server.register_function(modify, "modify")
server.register_function(provision, "provision")
server.register_function(terminate, "terminate")
server.serve_forever()
