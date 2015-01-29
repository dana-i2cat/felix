import xmlrpclib
import amsoil.core.pluginmanager as pm
import amsoil.core.log
# import pytz
from datetime import datetime, timedelta

logger = amsoil.core.log.getLogger('tnrmgeniv3delegate')
GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')

# from config import Config, Node, Interface, TNRM_Exception
from reservation import Request, Reservation
# from nsi2interface import *

# TNRM_CONFIG = 'src/vendor/tnrm/config.xml'
TNRM_PROXY = 'http://localhost:24444/'
nsi_proxy = xmlrpclib.ServerProxy(TNRM_PROXY)

dict_manifest = {}
dict_urn_rid = {}
dict_urn_endtime = {}
dict_urn_rspec = {}
dict_urn_astatus = {}
dict_urn_ostatus = {}

# epoch = datetime.fromtimestamp(0, pytz.timezone('Asia/Tokyo'))
epoch = datetime.utcfromtimestamp(0)

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
        # logger.info("list_resource:geni_available:%s" % (geni_available))

        rspec = nsi_proxy.get_advertisement()
        logger.info("advertisement=%s" % (rspec))
        return "%s" % (rspec)

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("slice_urn=" + slice_urn)
        # logger.info("client_cert=" + client_cert)
        # logger.info("credentials=" + credentials)
        logger.info("request rspec=" + rspec)
        # logger.info("end_time=" + end_time)

        start_time = datetime.utcnow()
        if (isinstance(end_time, type(None)) == True):
            end_time = start_time + timedelta(hours=1)
        else:
            delta = end_time - start_time
            if (delta.days * 24 * 3600 + delta.seconds < 60):
                end_time = start_time + timedelta(secounds=60)
                
        start_time_sec = unix_time_sec(start_time)
        end_time_sec = unix_time_sec(end_time)
        rid = nsi_proxy.reserve(rspec, start_time_sec, end_time_sec)
        logger.info("urns=%s, rid=%s" % (slice_urn, rid))

        dict_urn_rid[slice_urn] = rid
        dict_urn_endtime[slice_urn] = end_time
        dict_urn_rspec[slice_urn] = rspec
        dict_urn_astatus[slice_urn] = self.ALLOCATION_STATE_ALLOCATED
        dict_urn_ostatus[slice_urn] = self.OPERATIONAL_STATE_READY

        sliver = {"description": "test describe geniv3 method",
                  "ref": "geni site",
                  "email": "hoge @ aist.go.jp",
                  "slice_urn": slice_urn,
                  "reservationId": rid}

        slivers = [{'geni_sliver_urn': sliver,
                   'geni_expires': end_time,
                   'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                   'geni_operational_status': self.OPERATIONAL_STATE_READY,
                   'geni_error': ""}]

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

        manifest = nsi_proxy.get_manifest(rid)
        dict_manifest[slice_urn] = manifest

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return (manifest, slivers)

    gomi = """
    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

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

    def __sliver_describe_status(self, urn):
        if self.urn_type(urn) == "slice":
              rid = dict_urn_rid[urn]
              endtime = dict_urn_endtime[urn]
              astatus = dict_urn_astatus[urn]
              ostatus = dict_urn_ostatus[urn]
              
              return {'geni_sliver_urn': urn,
                      'geni_expires': endtime,
                      'geni_allocation_status': astatus,
                      'geni_operational_status': ostatus,
                      'geni_error': ""}

    @enter_method_log
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # logger.info("list_resource:urns:" + urns)
        # logger.info("list_resource:client_cert:" + client_cert)
        # logger.info("list_resource:credentials:" + credentials)

        slivers = [self.__sliver_describe_status(u) for u in urns]

        last_slice_urn = ""
        for u in urns:
              last_slice_urn = u
              # print "urn =%s" % (u)

        sliver = self.__sliver_describe_status(last_slice_urn)
        manifest = dict_manifest[last_slice_urn]
        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {'geni_rspec': manifest,
                'geni_urn': last_slice_urn,
                'geni_slivers': None}

    def __sliver_renew_status(self, urn, end_time, end_time_sec):
        if self.urn_type(urn) == "slice":

              # print "renew urn=%s" % (urn)
              rid = dict_urn_rid[urn]
              # print "rid=" + rid
              rid = nsi_proxy.modify(rid, end_time_sec)
        
              dict_urn_endtime[urn] = end_time
              astatus = dict_urn_astatus[urn]
              ostatus = dict_urn_ostatus[urn]
              
              sliver = {"description": "test describe geniv3 method",
                        "ref": "geni site",
                        "email": "hoge @ aist.go.jp",
                        "slice_urn": urn,
                        "reservationId": rid}
              
              return {'geni_sliver_urn': sliver,
                      'geni_expires': end_time,
                      'geni_allocation_status': astatus,
                      'geni_operational_status': ostatus,
                      'geni_error': ""}

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # print "urns=%s" % (urns[0])
        # print "client_cert=" + client_cert
        # print "credentials=" + credentials
        # print "best_effort=%s" % (best_effort)
        # print "expiration_time=%s" %(expiration_time)

        end_time_sec = unix_time_sec(expiration_time)
        slivers = [self.__sliver_renew_status(u, expiration_time, end_time_sec) for u in urns]


        logger.info("Slivers=%s" % (slivers))
        return slivers

    def __sliver_provision_status(self, urn):
        if self.urn_type(urn) == "slice":
              # print "provision urn=%s" % (urn)
              rid = dict_urn_rid[urn]
              end_time = dict_urn_endtime[urn]
              rspec = dict_urn_rspec[urn]
                # print "rid=" + rid
              st = dict_urn_astatus[urn]

              if (st == self.ALLOCATION_STATE_PROVISIONED):
                    logger.info("urn is already provisiond. urn=%s" % (urn))
              else:
                    nsi_proxy.provision(rid)
                    
              dict_urn_astatus[urn] = self.ALLOCATION_STATE_PROVISIONED
              dict_urn_ostatus[urn] = self.OPERATIONAL_ACTION_START

              sliver = {"description": "test describe geniv3 method",
                        "ref": "geni site",
                        "email": "hoge @ aist.go.jp",
                        "slice_urn": urn,
                        "reservationId": rid}
          
              return {'geni_sliver_urn': sliver,
                      'geni_expires': end_time,
                      'geni_allocation_status': dict_urn_astatus[urn],
                      'geni_operational_status': dict_urn_ostatus[urn],
                      'geni_error': ""}  
    
    @enter_method_log
    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase. """
        # print "urns=%s" % (urns[0])
        # print "client_cert=" + client_cert
        # print "credentials=" + credentials
        # print "best_effort=%s" % (best_effort)
        # print "end_time=%s" % (end_time)
        # print "geni_users=%s" % (geni_users)

        slivers = [self.__sliver_provision_status(u) for u in urns]

        logger.info("Slivers=%s" % (slivers))
        rspec = dict_urn_rspec[urns[0]]
        return rspec, slivers

    def __sliver_status(self, urn):
        if self.urn_type(urn) == "slice":
              end_time = dict_urn_endtime[urn]
              astatus = dict_urn_astatus[urn]
              ostatus = dict_urn_ostatus[urn]

              return {'geni_sliver_urn': urn, 
                      'geni_expires': end_time,
                      'geni_allocation_status': astatus,
                      'geni_operational_status': ostatus,
                      'geni_error': ""}

    @enter_method_log
    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        slivers = [self.__sliver_status(d) for d in urns]
        logger.info("Slivers=%s" % (slivers))
        return "status-slice_urns", slivers

    def __sliver_operational_status(self, urn, action):
        if self.urn_type(urn) == "slice":
              end_time = dict_urn_endtime[urn]
              astatus = dict_urn_astatus[urn]
              ostatus = dict_urn_ostatus[urn]

              return {'geni_sliver_urn': urn,
                      'geni_expires': end_time,
                      'geni_allocation_status': astatus,
                      'geni_operational_status': ostatus,
                      'geni_error': "",
                      'geni_resource_status': "we do not need action:" + action + "."}

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        slivers = [self.__sliver_operational_status(u, action) for u in urns]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    def __sliver_delete_status(self, urn, now):
        if self.urn_type(urn) == "slice":
              # print "delete urn=%s" % (urn)
              rid = dict_urn_rid[urn]
              # print "rid=" + rid
              nsi_proxy.terminate(rid)

              sliver = {"description": "test describe geniv3 method",
                        "ref": "geni site",
                        "email": "hoge @ aist.go.jp",
                        "slice_urn": urn,
                        "reservationId": rid}

              del dict_manifest[urn]
              del dict_urn_rid[urn]
              end_time = dict_urn_endtime[urn]
              del dict_urn_endtime[urn]
              del dict_urn_rspec[urn]
              del dict_urn_astatus[urn]
              del dict_urn_ostatus[urn]

              return {'geni_sliver_urn': sliver,
                      'geni_expires': end_time,
                      'geni_allocation_status': self.ALLOCATION_STATE_UNALLOCATED,
                      'geni_operational_status': self.OPERATIONAL_STATE_NOTREADY,
                      'geni_error': ""}  

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # print "urns=%s" % (urns)
        # print "client_cert=" + client_cert
        # print "best_effort=%s" % (best_effort)

        # now = datetime.now(pytz.timezone('Asia/Tokyo'))
        now = datetime.utcnow()
        slivers = [self.__sliver_delete_status(u, now) for u in urns]

        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        now = datetime.utcnow()
        sliver = self.__sliver_delete_status(slice_urn, now)
        return sliver
