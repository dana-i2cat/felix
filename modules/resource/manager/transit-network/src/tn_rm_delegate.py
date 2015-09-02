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

import xmlrpclib
import amsoil.core.pluginmanager as pm
import amsoil.core.log
logger = amsoil.core.log.getLogger('TN-RM')

# import pytz
from datetime import datetime, timedelta

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')

# from config import Config, Node, Interface, TNRM_Exception
from reservation import Request, Reservation
import tn_rm_exceptions as tnex
# from nsi2interface import *

# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
TNRM_PROXY = 'http://localhost:24444/'
nsi_proxy = xmlrpclib.ServerProxy(TNRM_PROXY)
geni_sliver_urn = 'urn:publicid:tn-network1:'

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
    # print "timezone=%s" % (dt.tzinfo)
    return int(delta.total_seconds())

class TNRMGENI3Delegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:SDNRM_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/3'

    def __init__(self):
        super(TNRMGENI3Delegate, self).__init__()
        logger.info("TNRMGENI3Delegate successfully initialized!")
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

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("list_resource:client_cert:" + client_cert)
        # logger.info("list_resource:credentials:" + credentials)
        logger.info("list_resource:geni_available:%s" % (geni_available))

        rspec = nsi_proxy.get_advertisement()
        logger.info("advertisement=%s" % (rspec))
        return "%s" % (rspec)

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        logger.info("slice_urn=%s" % (slice_urn))
        # logger.info("client_cert=%s" % (client_cert))
        # logger.info("credentials=%s" % (credentials))
        logger.info("request rspec=%s" % (rspec))
        logger.info("end_time=%s" % (end_time))

        start_time = datetime.utcnow()
        # start_time = datetime.now()
        if (isinstance(end_time, type(None)) == True):
            end_time = start_time + timedelta(hours=1)
        else:
            delta = end_time - start_time
            logger.debug("delta days=%s, seconds=%s" % (delta.days, delta.seconds))
            if (delta.days * 24 * 3600 + delta.seconds < 60):
                end_time = start_time + timedelta(seconds=60)
                logger.debug("re-set end_time=%s" % (end_time))
                
        start_time_sec = unix_time_sec(start_time)
        end_time_sec = unix_time_sec(end_time)
        logger.info("call reserve start_time=%s, end_time=%s" % 
                    (self.__datetime2str(start_time), self.__datetime2str(end_time)))

        rid = None
        slivers = [{}]
        manifest = None

        try:
              rid = nsi_proxy.reserve(rspec, start_time_sec, end_time_sec)
              logger.info("urns=%s, rid=%s" % (slice_urn, rid))

              dict_urn_rid[slice_urn] = rid
              dict_urn_endtime[slice_urn] = end_time
              dict_urn_rspec[slice_urn] = rspec
              dict_urn_ostatus[slice_urn] = self.OPERATIONAL_STATE_READY
              dict_urn_astatus[slice_urn] = self.ALLOCATION_STATE_ALLOCATED
              dict_urn_pstatus[slice_urn] = self.OPERATIONAL_ACTION_STOP

        except Exception as e:
              rid = None
              logger.error("%s" % (e))
              slivers = [{
                    'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                    'geni_expires': end_time,
                    'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': slice_urn,
                    'geni_error': ("%s" % (e))
                    }]

        if rid is not None:
            slivers = [{
                    'geni_operational_status': self.OPERATIONAL_STATE_READY,
                    'geni_expires': end_time,
                    # 'geni_expires': self.__datetime2str(end_time),
                    'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': slice_urn,
                    # 'geni_error': ""
                    }]

            try:
                manifest = nsi_proxy.get_manifest(rid)
                dict_manifest[slice_urn] = manifest
            except Exception as e:
                logger.error("ex=%s,\nManifest=%s,\nSlivers=%s" % (e, manifest, slivers))
                manifest = None

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return (manifest, slivers)

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    def __sliver_describe_status(self, urn):
        if self.urn_type(urn) == "slice":
              rid = dict_urn_rid[urn]
              end_time = dict_urn_endtime[urn]
              astatus = dict_urn_astatus[urn]
              ostatus = dict_urn_ostatus[urn]
              
              return {
                  'geni_operational_status': ostatus,
                  # 'geni_expires': end_time,
                  'geni_expires': self.__datetime2str(end_time),
                  'geni_allocation_status': astatus,
                  'geni_sliver_urn': geni_sliver_urn,
                  'geni_nrn': urn,
                  'geni_error': ""
                  }

    @enter_method_log
    def describe(self, urns, credentials, options):
    #def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("describe:urns:" + urns)
        # logger.info("describe:credentials:" + credentials)

        slivers = [self.__sliver_describe_status(u) for u in urns]

        last_slice_urn = ""
        for u in urns:
              last_slice_urn = u
              logger.info("urn =%s" % (u))
              break

        sliver = self.__sliver_describe_status(last_slice_urn)
        manifest = dict_manifest[last_slice_urn]
        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {'geni_rspec': manifest,
                'geni_urn': last_slice_urn,
                'geni_slivers': slivers}

    def __sliver_renew_status(self, urn, end_time, end_time_sec):
        rid = None
        astatus = None
        ostatus = None
        sliver = {}

        logger.debug("renew urn=%s" % (urn))

        try:
            if self.urn_type(urn) == "slice":
                rid = dict_urn_rid[urn]
                logger.debug("rid=%s" % (rid))
                
                astatus = dict_urn_astatus[urn]
                ostatus = dict_urn_ostatus[urn]
                logger.info("allocate=%s, operation=%s" % (astatus, ostatus))
        except Exception as e:
            rid = None

        logger.debug("rid=%s" % (rid))

        if rid is not None:
            try:
                rid = nsi_proxy.modify(rid, end_time_sec)
                logger.info("old is %s, new is %s" %(dict_urn_rid[urn], rid))
                dict_urn_endtime[urn] = end_time

                sliver = {
                    'geni_operational_status': ostatus,
                    'geni_expires': end_time,
                    'geni_allocation_status': astatus,
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': urn,
                    }
            except Exception as e:
                end_time = dict_urn_endtime[urn]
                sliver = {
                    'geni_operational_status': ostatus,
                    'geni_expires': end_time,
                    'geni_allocation_status': astatus,
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': urn,
                    'geni_error': ("%s" % (e))
                    }
        logger.info("sliver is %s" % (sliver))

        aho = """
            else:
            sliver = {
                'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                'geni_expires': end_time,
                'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                'geni_sliver_urn': geni_sliver_urn,
                'geni_nrn': urn,
                # 'geni_error': ("There is no allocated resoure.")
                } """
        return sliver

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
        slivers = [self.__sliver_renew_status(u, expiration_time, end_time_sec) for u in urns]
        
        
        logger.info("Slivers=%s" % (slivers))
        return slivers

    def __sliver_provision_status(self, urn):
        rid = None
        logger.debug("renew urn=%s" % (urn))
        end_time = None
        astatus = None
        ostatus = None
        sliver = {}

        try:
            if self.urn_type(urn) == "slice":
                rid = dict_urn_rid[urn]

                astatus = dict_urn_astatus[urn]
                ostatus = dict_urn_ostatus[urn]
                logger.info("allocate=%s, operation=%s" % (astatus, ostatus))
        except Exception as e:
            rid = None

        logger.debug("rid=%s" % (rid))

        if rid is not None:
            end_time = dict_urn_endtime[urn]
            rspec = dict_urn_rspec[urn]
            st = dict_urn_astatus[urn]

            if (st == self.ALLOCATION_STATE_PROVISIONED):
                logger.info("urn is already provisiond. urn=%s" % (urn))
            else:
                dict_urn_astatus[urn] = self.ALLOCATION_STATE_PROVISIONED
                dict_urn_ostatus[urn] = self.OPERATIONAL_STATE_READY
                dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_STOP

            sliver = {
                'geni_operational_status': dict_urn_ostatus[urn],
                'geni_expires': end_time,
                'geni_end_time': self.__datetime2str(end_time),
                'geni_allocation_status': dict_urn_astatus[urn],
                'geni_sliver_urn': geni_sliver_urn,
                'geni_nrn': urn,
                }
        else:
            ctime = datetime.utcnow()
            sliver = {
                'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                'geni_expires': ctime,
                # 'geni_end_time': ctime,
                'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                'geni_sliver_urn': geni_sliver_urn,
                'geni_nrn': urn,
                # 'geni_error': "There is no allocated resource."
                }
            
        return sliver
    
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

        slivers = [self.__sliver_provision_status(u) for u in urns]

        logger.info("Slivers=%s" % (slivers))

        rspec = None

        try:
            rspec = dict_manifest[urns[0]]
        except:
            rspec = """<?xml version="1.1" encoding="UTF-8"?>
<rspec type="manifest"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:stitch="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://hpn.east.isi.edu/rspec/ext/stitch/0.1/
            http://hpn.east.isi.edu/rspec/ext/stitch/0.1/stitch-schema.xsd
            http://www.geni.net/resources/rspec/3/manifest.xsd
            http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">
</rspce>"""

        return rspec, slivers

    def __sliver_status(self, urn):
        sliver = None

        try :
            if self.urn_type(urn) == "slice":
                end_time = dict_urn_endtime[urn]
                astatus = dict_urn_astatus[urn]
                ostatus = dict_urn_ostatus[urn]
                
                sliver = {
                    'geni_operational_status': ostatus,
                    'geni_expires': end_time,
                    'geni_allocation_status': astatus,
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': urn,
                    }
        except Exception as e:
            pass

        if sliver is None:
            ctime = datetime.utcnow()
            sliver = {
                'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                'geni_expires': ctime,
                'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                'geni_sliver_urn': geni_sliver_urn,
                'geni_nrn': urn,
                }

        return sliver
            
    @enter_method_log
    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        slivers = [self.__sliver_status(d) for d in urns]
        logger.info("Slivers=%s" % (slivers))
        return "status-slice_urns", slivers

    def __sliver_operational_status(self, urn, action):
        sliver = None

        try:
            if self.urn_type(urn) == "slice":
                rid = dict_urn_rid[urn]

                end_time = dict_urn_endtime[urn]
                astatus = dict_urn_astatus[urn]
                ostatus = dict_urn_ostatus[urn]
                pstatus = dict_urn_pstatus[urn]

                if astatus != self.ALLOCATION_STATE_PROVISIONED:
                    sliver = {
                        'geni_operational_status': dict_urn_ostatus[urn],
                        'geni_expires': end_time,
                        'geni_allocation_status': dict_urn_astatus[urn],
                        'geni_sliver_urn': geni_sliver_urn,
                        'geni_nrn': urn,
                        'geni_error': "Not ALLOCATION_STATE_PROVISIONED.",
                        }
                    logger.info("Not ALLOCATION_STATE_PROVISIONED.")
                    return sliver


                if action == "start":
                    if pstatus == self.OPERATIONAL_ACTION_STOP:
                        nsi_proxy.provision(rid)
                        dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_START
                        dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_START
                        logger.info("NSI PROVISIONED.")

                elif action == "stop":
                    if pstatus == self.OPERATIONAL_ACTION_START:
                        nsi_proxy.release(rid)
                        dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_STOP
                        dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_STOP
                        logger.info("NSI RELEASE.")

                elif action == "restart":
                    if pstatus == self.OPERATIONAL_ACTION_START:
                        nsi_proxy.release(rid)
                        dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_STOP
                        dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_STOP
                        logger.info("NSI RELEASE.")

                        nsi_proxy.provision(rid)
                        dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_START
                        dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_START
                        logger.info("NSI PROVISIONED.")

                    if pstatus == self.OPERATIONAL_ACTION_STOP:
                        nsi_proxy.provision(rid)
                        dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_START
                        dict_urn_pstatus[urn] = self.OPERATIONAL_ACTION_START
                        logger.info("NSI PROVISIONED.")

                else:
                    sliver = {
                        'geni_operational_status': dict_urn_ostatus[urn],
                        'geni_expires': end_time,
                        'geni_allocation_status': dict_urn_astatus[urn],
                        'geni_sliver_urn': geni_sliver_urn,
                        'geni_nrn': urn,
                        'geni_error': ("Unknown operation action(%s)." % (action)),
                        }
                    logger.info("Unknown operation action(%s)." % (action))
                    return sliver

                sliver = {
                    'geni_operational_status': dict_urn_ostatus[urn],
                    'geni_expires': end_time,
                    'geni_allocation_status': dict_urn_astatus[urn],
                    'geni_sliver_urn': geni_sliver_urn,
                    'geni_nrn': urn,
                    }

        except Exception as e:
            ctime = datetime.utcnow()
            sliver = {
                'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                'geni_expires': ctime,
                'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                'geni_sliver_urn': geni_sliver_urn,
                'geni_nrn': urn,
                'geni_error': ("%s" % (e)),
                }
            logger.info("Exception %s" % (e))

        return sliver

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        slivers = [self.__sliver_operational_status(u, action) for u in urns]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    def __sliver_delete_status(self, urn, now):
          rid = None
          end_time = datetime.utcnow()
          sliver = None

          sliver = {
              'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
              'geni_expires': end_time,
              'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
              'geni_sliver_urn': geni_sliver_urn,
              'geni_nrn': urn,
              }

          if self.urn_type(urn) == "slice":
              # logger.debug("delete urn=%s" % (urn))
              try:
                    rid = dict_urn_rid[urn]
              except Exception as e:
                    rid = None

          if rid is not None:
              try:
                  nsi_proxy.terminate(rid)

                  del dict_manifest[urn]
                  del dict_urn_rid[urn]
                  end_time = dict_urn_endtime[urn]
                  del dict_urn_endtime[urn]
                  del dict_urn_rspec[urn]
                  del dict_urn_astatus[urn]
                  del dict_urn_ostatus[urn]
                  del dict_urn_pstatus[urn]

                  logger.debug("rid=%s, end_time=%s" % (rid, end_time))
                  sliver = {
                      'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                      'geni_expires': end_time,
                      'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                      'geni_sliver_urn': geni_sliver_urn,
                      'geni_nrn': urn,
                      }  
              except Exception as e:
                  sliver = {
                      'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                      'geni_expires': end_time,
                      'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                      'geni_sliver_urn': geni_sliver_urn,
                      'geni_nrn': urn,
                      'geni_error': ("%s" % (e))
                      }

          return sliver

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.debug("urns=%s" % (urns))
        # logger.debug("client_cert=%s" % (client_cert))
        # logger.debug("best_effort=%s" % (best_effort))

        # now = datetime.now(pytz.timezone('Asia/Tokyo'))
        now = datetime.utcnow()
        slivers = [self.__sliver_delete_status(u, now) for u in urns]

        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        now = datetime.utcnow()
        slivers = [self.__sliver_delete_status(slice_urn, now)]
        return slivers

    gomi = """
    def __test_urns(self, urns, offset):
        dpids, last_urn = [], ""
        for urn in urns:
            if self.urn_type(urn) == "slice":
                last_urn = urn

            dpids.append(
                {"component_id": "test-sliver_%d" % (len(dpids) + offset)})
        return dpids, last_urn

    def __test_datapaths(self, dpids):
        if len(dpids) == 0:
            raise geni_ex.GENIv3SearchFailedError(
                "No resources in the given slice-urns")

    def __sliver_str_status(self, dpid):
        return {'geni_sliver_urn': dpid.get("component_id"),
                'geni_expires': self.__datetime2str(datetime.datetime.now()),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': ""}

    def __sliver_date_status(self, dpid):
        return {'geni_sliver_urn': dpid.get("component_id"),
                'geni_expires': datetime.datetime.now(),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': ""}

    def __sliver_details_status(self, dpid):
        cid = dpid.get("component_id")
        return {'geni_sliver_urn': cid,
                'geni_expires': datetime.datetime.now(),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': "",
                'geni_resource_status': "some-details-%s" % cid}

    def __manifest(self, sliver):
        mr = self.lxml_manifest_root()
        em = self.lxml_manifest_element_maker('openflow')

        ref = "Pending" if sliver.get("ref") is None else sliver.get("ref")

        s = em.sliver(email=sliver.get("email"),
                      description=sliver.get("description"),
                      ref=ref)
        mr.append(s)

        return mr
    """

