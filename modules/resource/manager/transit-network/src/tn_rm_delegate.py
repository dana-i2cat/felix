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
import sys

import xmlrpclib
import amsoil.core.pluginmanager as pm
import amsoil.core.log
logger = amsoil.core.log.getLogger('TN-RM')

# import pytz
from datetime import datetime, timedelta

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')

# from config import Config, Node, Interface
from reservation import Request, Reservation, Advertisement
from ovsgre import ovs_proxy
from tn_rm_exceptions import ManagerException, ParamException

# import tn_rm_exceptions as tnex
# from nsi2interface import *

TNRM_PROXY = 'http://localhost:24444/'
nsi_proxy = xmlrpclib.ServerProxy(TNRM_PROXY)
geni_sliver_urn = 'urn:publicid:tn-network1:'
gre_proxy = ovs_proxy()

#
# from config import Config
# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
# config = Config(TNRM_CONFIG)

dict_slice_urn = {}

dict_manifest = {}
dict_urn_rid = {}
dict_urn_endtime = {}
dict_urn_rspec = {}
dict_urn_astatus = {}
dict_urn_ostatus = {}
dict_urn_pstatus = {}

# epoch = datetime.fromtimestamp(0, pytz.timezone('Asia/Tokyo'))
epoch = datetime.utcfromtimestamp(0)

# ALLOCATION_STATE_UNALLOCATED
# ALLOCATION_STATE_ALLOCATED
# ALLOCATION_STATE_PROVISIONED

# OPERATIONAL_STATE_PENDING_ALLOCATION
# OPERATIONAL_STATE_NOTREADY
# OPERATIONAL_STATE_CONFIGURING
# OPERATIONAL_STATE_STOPPING
# OPERATIONAL_STATE_READY
# OPERATIONAL_STATE_READY_BUSY
# OPERATIONAL_STATE_FAILED
# OPERATIONAL_ACTION_START
# OPERATIONAL_ACTION_RESTART
# OPERATIONAL_ACTION_STOP

def unix_time_sec(dt):
    delta = dt - epoch
    logger.info("timezone=%s" % (dt.tzinfo))
    return int(delta.total_seconds())

class TNRMGENI3Delegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:SDNRM_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/3'

    def __init__(self):
        super(TNRMGENI3Delegate, self).__init__()
        logger.info("TNRMGENI3Delegate successfully initialized!")
        self.adv = Advertisement()
        self.advertisement = self.adv.get_advertisement()
        # self.config = Config(TNRM_CONFIG)
        # self.nsi = NSI()

    def enter_method_log(f):
        as_ = f.func_code.co_varnames[:f.func_code.co_argcount]

        def wrapper(*args, **kwargs):
            ass_ = ', '.join('%s=%r' % e for e in zip(as_, args) +
                             kwargs.items())
            logger.info("Calling %s with args=%s" % (f.func_name, ass_,))
            return f(*args, **kwargs)
        return wrapper

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("list_resource:client_cert:" + client_cert)
        # logger.info("list_resource:credentials:" + credentials)
        logger.info("list_resource:geni_available:%s" % (geni_available))

        # rspec = config.get_advertisement()
        rspec = self.advertisement
        logger.info("advertisement=%s" % (rspec))
        return "%s" % (rspec)

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.info("slice_urn=%s" % (slice_urn))
        logger.info("client_cert=%s" % (client_cert))
        logger.info("credentials=%s" % (credentials))
        logger.info("request rspec=%s" % (rspec))
        logger.info("end_time=%s" % (end_time))

        start_time = datetime.utcnow()
        # start_time = datetime.now()
        start_time += timedelta(minutes=2)
        if (isinstance(end_time, type(None)) == True):
            end_time = start_time + timedelta(minutes=10)
            end_time = start_time + timedelta(hours=3)
        else:
            delta = end_time - start_time
            logger.debug("delta days=%s, seconds=%s" % (delta.days, delta.seconds))
            if (delta.days * 24 * 3600 + delta.seconds < 60):
                end_time = start_time + timedelta(seconds=60)
                logger.debug("re-set end_time=%s" % (end_time))
                
        start_time_sec = unix_time_sec(start_time)
        end_time_sec = unix_time_sec(end_time)

        req = Request(slice_urn, rspec, start_time, end_time)
        req, error = req.parse_reservations()
        if error is not None:
            raise geni_ex.GENIv3GeneralError(error)
        logger.info("slice=%s, urns=%s" % (slice_urn, str(req.urns)))

        if slice_urn in dict_slice_urn:
            raise geni_ex.GENIv3GeneralError("slice_urn(%s) is already exit." % (slice_urn))

        logger.info("allocate: add dict_slice_urn[%s]." % slice_urn)
        dict_slice_urn[slice_urn] = req

        for urn in req.urns:
            resv = req.get_reservation(urn)
            resv.ostatus = self.OPERATIONAL_STATE_NOTREADY
            resv.astatus = self.ALLOCATION_STATE_UNALLOCATED
            resv.action = self.OPERATIONAL_ACTION_STOP

        slice_status = req.get_status()
        manifest = req.get_manifest()

        isError = False
        for urn in req.urns:
            resv = req.get_reservation(urn)
            logger.info("call reserve %s" % (resv))

            #
            # VLAN range check in Reservation
            #

            try:
                if resv.service == "NSI":
                    rid = nsi_proxy.reserve(resv.gid,
                                            resv.path.sep.stp, 
                                            resv.path.dep.stp,
                                            int(resv.path.sep.vlantag), 
                                            int(resv.path.dep.vlantag), 
                                            int(resv.path.sd_bw), 
                                            unix_time_sec(start_time), 
                                            unix_time_sec(end_time))

                elif resv.service == "GRE":
                    rid = gre_proxy.reserve(resv)

                else:
                    emes = "Unknown service=%s: urn=%s, type=$s, reservation=%s" % (resv.service, slice_urn, resv)
                    logger.error(emes)
                    raise ManagerException("tn_rm_delegate:allocate", emes);
                    
                logger.info("urns=%s, rid=%s" % (slice_urn, rid))

                resv.resv_id = rid
                resv.astatus = self.ALLOCATION_STATE_ALLOCATED
                resv.ostatus = self.OPERATIONAL_STATE_READY
                resv.action = self.OPERATIONAL_ACTION_STOP

            except Exception as e:
                logger.error("ex=%s" % (e))
                resv.error = "%s" % (e)
                isError = True
                    
        if isError:
            now = datetime.utcnow()
            self.__slice_delete_status(slice_urn, now)

        slice_status = req.get_status()
        manifest = req.get_manifest()
        return (manifest, slice_status)

    def __slice_status(self, urn):
        if self.urn_type(urn) == "slice":
            logger.info("urn (%s) is a slice." % (urn))
            if urn in dict_slice_urn:
                req = dict_slice_urn[urn]
                slice_status = req.get_status()
                return slice_status
            else:
                logger.info("urn (%s) is aslice." % (urn)) 
        return None

    @enter_method_log
    def describe(self, urns, credentials, options):
    #def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("describe:urns:" + urns)
        # logger.info("describe:credentials:" + credentials)

        last_slice = None
        req = None
        manifest = None
        slice_status = []

        for urn in urns:
            if self.urn_type(urn) == "slice":
                logger.info("urn (%s) is a slice." % (urn))
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn
                else:
                    logger.info("urn (%s) is not in dict_slice_urn." % (urn)) 

        if req is not None:
            manifest = req.get_manifest()
            slice_status = req.get_status()
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))
        logger.info("manifest=%s, status=%s" % (manifest, slice_status))
        return {'geni_rspec': manifest,
                'geni_urn': last_slice,
                'geni_slivers': slice_status}

    def __sliver_renew_status(self, urn, end_time, end_time_sec):
        logger.debug("renew urn=%s" % (urn))

        req = dict_slice_urn[urn]
        for u in req.urns:
            resv = req.get_reservation(u)
            if resv.astatus == self.ALLOCATION_STATE_UNALLOCATED:
                continue

            rid = resv.resv_id
            
            try:
                if resv.service == "NSI":
                    mid = nsi_proxy.modify(resv.gid, rid, end_time_sec)
                elif resv.service == "GRE":
                    mid = gre_proxy.modify(resv, end_time_sec)
                else:
                    logger.error("Unknown service=%s: urn=%s, type=$s, reservation=%s" % 
                                 (resv.service, u, resv))

                logger.info("old is %s, new is %s" %(rid, mid))
                resv.end_time = end_time
                resv.error = None

            except Exception as e:
                logger.error("%s" % (e))
                resv.error = "%s" % (e)

        slice_status = req.get_status()
        return slice_status

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.debug("urns=%s" % (urns[0]))
        # logger.debug("client_cert=%s" % (client_cert))
        # logger.debug("credentials=%s" % 'credentials))
        # logger.debug("best_effort=%s" % (best_effort))
        # logger.debug("expiration_time=%s" % (expiration_time))

        end_time_sec = unix_time_sec(expiration_time)

        last_slice = None
        req = None
        manifest = None
        slice_status = []

        for urn in urns:
            if self.urn_type(urn) == "slice":
                logger.info("urn (%s) is a slice." % (urn))
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn
                else:
                    logger.info("urn (%s) is not in dict_slice_urn." % (urn)) 

        if req is not None:
            self.__sliver_renew_status(last_slice, expiration_time, end_time_sec)
            slice_status = req.get_status()
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))
        logger.info("status=%s" % (slice_status))
        return slice_status

    def __slice_provision_status(self, urn):
        req = dict_slice_urn[urn]
        for u in req.urns:
            resv = req.get_reservation(u)
            if resv.astatus == self.ALLOCATION_STATE_UNALLOCATED:
                continue

            resv.astatus = self.ALLOCATION_STATE_PROVISIONED
            resv.ostatus = self.OPERATIONAL_STATE_READY
            resv.action = self.OPERATIONAL_ACTION_STOP

        slice_status = req.get_status()
        return slice_status
    
    @enter_method_log
    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase. """
        # logger.debug("urns=%s" % (urns[0]))
        # logger.debug("client_cert=%s" % (client_cert))
        # logger.debug("credentials=%s" % (credentials))
        # logger.debug("best_effort=%s" % (best_effort))
        # logger.debug("end_time=%s" % (end_time))
        # logger.debug("geni_users=%s" % (geni_users))

        last_slice = None
        req = None
        manifest = None
        slice_status = []

        for urn in urns:
            if self.urn_type(urn) == "slice":
                logger.info("urn (%s) is a slice." % (urn))
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn
                else:
                    logger.info("urn (%s) is not in dict_slice_urn." % (urn)) 

        if req is not None:
            slice_status = self.__slice_provision_status(last_slice)
            manifest = req.get_manifest()
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))
        logger.info("status=%s" % (slice_status))
        return (manifest, slice_status)

    @enter_method_log
    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rule_error = None

        for urn in urns:
            if self.urn_type(urn) == "slice":
                logger.info("urn (%s) is a slice." % (urn))
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn

                    for u in req.urns:
                        resv = req.get_reservation(u)
                        logger.info("status: urn=%s, resv=%s" % (u, resv))
                        if resv is not None:
                            logger.info("status:check rule now.")
                            rc = self.__proxy_check_rule(resv, u)
                            if not rc:
                                logger.info("status:check rule is %s" % (rc)) 
                                rule_error = "mis match openflow rule in Open vSwitch, try poa geni_restart"
                                keep_error = resv.error
                                resv.error = rule_error
                                slice_status = req.get_status()
                                resv.error = keep_error
                                
                                return "status-slice_urns", slice_status
                            else:
                                logger.info("status: flow rule is OK.")
                        else:
                            logger.info("status:skip check as resv is None.")
                else:
                    logger.info("urn (%s) is not in dict_slice_urn." % (urn)) 
            else:
                logger.info("urn type is not slice, but (%s)." % (self.urn_type(urn)))

        if req is not None:
            manifest = req.get_manifest()
            slice_status = req.get_status()
            logger.info("status: %s" % slice_status)
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))

        return "status-slice_urns", slice_status

    def __proxy_setup_path(self, resv, urn):
        logger.info("service type=%s" % (resv.service)); 
        try:
            if resv.service == "NSI":
                nsi_proxy.provision(resv.resv_id)
                logger.info("NSI PROVISIONED.")
            elif resv.service == "GRE":
                gre_proxy.provision(resv)
                logger.info("GRE SETUP.")
            else:
                logger.error("Unknown service=%s: urn=%s, type=$s, reservation=%s" % 
                             (resv.service, urn, resv))

        except Exception as e:
            logger.error("%s" % (e))
            resv.error = "%s" % (e)

    def __proxy_teardown_path(self, resv, urn):
        logger.info("service type=%s" % (resv.service)); 
        try:
            if resv.service == "NSI":
                nsi_proxy.release(resv.resv_id)
                logger.info("NSI RELEASED.")
            elif resv.service == "GRE":
                gre_proxy.release(resv)
                logger.info("GRE TEARDOWN.")
            else:
                logger.error("Unknown service=%s: urn=%s, type=$s, reservation=%s" % 
                             (resv.service, urn, resv))
        except Exception as e:
            logger.error("%s" % (e))
            resv.error = "%s" % (e)
                
    def __proxy_check_rule(self, resv, urn):
        logger.info("operation status=%s" % (resv.action)); 
        if resv.action != self.OPERATIONAL_ACTION_START:
            return True

        logger.info("service type=%s" % (resv.service)); 
        try:
            if resv.service == "NSI":
                pass
            elif resv.service == "GRE":
                rc = gre_proxy.status(resv)
                if not rc:
                    return False
            else:
                logger.error("Unknown service=%s: urn=%s, type=$s, reservation=%s" % 
                             (resv.service, urn, resv))

        except Exception as e:
            logger.error("%s" % (e))
            resv.error = "%s" % (e)

        return True
                
    def __slice_operational_status(self, urn, action):
        req = dict_slice_urn[urn]

        for u in req.urns:
            resv = req.get_reservation(u)
            if resv.astatus == self.ALLOCATION_STATE_UNALLOCATED:
                continue

            # Carolina 2015/06/29: standardize POA actions to GENI expected
            # -- Keeping custom actions (start, stop) for backwards compatibility
            geni_start_action = ["geni_start", "start"]
            geni_stop_action = ["geni_stop", "stop"]
            geni_restart_action = ["geni_restart", "restart"]

            if resv.astatus == self.ALLOCATION_STATE_PROVISIONED:
                if any([ action == a for a in geni_start_action]):
                    if resv.action == self.OPERATIONAL_ACTION_STOP:
                        self.__proxy_setup_path(resv, u)
                        resv.action = self.OPERATIONAL_ACTION_START

                    # if resv.action == self.OPERATIONAL_ACTION_START:
                    #   self.__proxy_setup_path(resv, u)
                        
                elif any([ action == a for a in geni_stop_action]):
                    if resv.action == self.OPERATIONAL_ACTION_START:
                        self.__proxy_teardown_path(resv, u)
                        resv.action = self.OPERATIONAL_ACTION_STOP

                    # if resv.action == self.OPERATIONAL_ACTION_STOP:
                    #   __proxy_teardown_path(resv, u)

                elif any([ action == a for a in geni_restart_action]):
                    if resv.action == self.OPERATIONAL_ACTION_START:
                        self.__proxy_teardown_path(resv, u)
                        resv.action = self.OPERATIONAL_ACTION_STOP

                    if resv.action == self.OPERATIONAL_ACTION_STOP:
                        self.__proxy_setup_path(resv, u)
                        resv.action = self.OPERATIONAL_ACTION_START

                else:
                    logger.info("Unknown operation action(%s)." % (action))

        slice_status = req.get_status()
        return slice_status

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort): 
        req = None
        last_slice = None
        for urn in urns:
            if self.urn_type(urn) == "slice":
                logger.info("urn (%s) is a slice." % (urn))
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn
                else:
                    logger.info("urn (%s) is not in dict_slice_urn." % (urn)) 

        if req is not None:
            slice_status = self.__slice_operational_status(last_slice, action)
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))
        return slice_status

    def __slice_delete_status(self, urn, now):
        req = dict_slice_urn[urn]

        doneall = True

        for u in req.urns:
            resv = req.get_reservation(u)
            if resv.astatus == self.ALLOCATION_STATE_UNALLOCATED:
                continue
            
            logger.info("call terminate %s" % (resv))
            try:
                if resv.service == "NSI":
                    nsi_proxy.terminate(resv.resv_id)
                elif resv.service == "GRE":
                    gre_proxy.terminate(resv)
                else:
                    logger.error("Unknown service=%s: urn=%s, type=$s, reservation=%s" % 
                                 (resv.service, urn, resv))

                resv.astatus = self.ALLOCATION_STATE_UNALLOCATED
                resv.ostatus = self.OPERATIONAL_STATE_NOTREADY
                resv.action = self.OPERATIONAL_ACTION_STOP
                resv.end_time = now

            except Exception as e:
                logger.error("%s" % (e))
                resv.error = "%s" % (e)
                doneall = False

        slice_status = req.get_status()

        # if doneall:
        #    del dict_slice_urn[urn]
        del dict_slice_urn[urn]
        return slice_status

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.debug("urns=%s" % (urns))
        # logger.debug("client_cert=%s" % (client_cert))
        # logger.debug("best_effort=%s" % (best_effort))

        # now = datetime.now(pytz.timezone('Asia/Tokyo'))
        now = datetime.utcnow()
        slice_status = []
        req = None
        for urn in urns:
            if self.urn_type(urn) == "slice":
                if urn in dict_slice_urn:
                    req = dict_slice_urn[urn]
                    last_slice = urn
                else:
                    logger.info("This slice (%s) is not exist." % (urn))
            else:
                logger.info("This urn (%s) is not slice." % (urn))

        if req is not None:
            slice_status = self.__slice_delete_status(last_slice, now)
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (urn))
        return slice_status

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        now = datetime.utcnow()
        if slice_urn in dict_slice_urn:
            slice_status = self.__slice_delete_status(slice_urn, now)
        else:
            raise geni_ex.GENIv3GeneralError("This slice (%s) is not exist." % (slice_urn))
        return slice_status

if __name__ == "__main__":
    client_cert = "test client_cert"
    credentials = "test credentials"
    geni_acailable = "False"

    list_resources(client_cert, credentials, geni_available)
