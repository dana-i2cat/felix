from datetime import datetime, timedelta

import amsoil.core.pluginmanager as pm
import amsoil.core.log
logger=amsoil.core.log.getLogger('dhcpresourcemanager')

from ip import IP
from dhcpexceptions import *

worker = pm.getService('worker')
Schedule = pm.getService('schedule')
sex = pm.getService('scheduleexceptions')

class DHCPResourceManager(object):
    """
    This class provides the necessary functions to manage DHCP leases.
    Please see the wiki for more information on Resource Managers.
    
    In this resource manager, we are using simple python dicts to pass the data to the delegate.
    In a more sophisticated AM, one should probably define a decent class for passing the data.
    """
    config = pm.getService("config")

    RESERVATION_TIMEOUT = config.get("dhcprm.max_reservation_duration") # sec in the allocated state
    MAX_LEASE_DURATION = config.get("dhcprm.max_lease_duration") # sec in the provisioned state (you can always call renew)
    EXPIRY_CHECK_INTERVAL = 10 # sec

    ip_schedule = Schedule("DHCPLease", MAX_LEASE_DURATION)
    
    def __init__(self):
        super(DHCPResourceManager, self).__init__()
        # register callback for regular updates
        worker.addAsReccurring("dhcpresourcemanager", "expire_leases", None, self.EXPIRY_CHECK_INTERVAL)
    
    def get_all_leases(self):
        valuedicts = []
        for ip in IP([192,168,1,1]).upto(IP([192,168,1,20])): # for the sake of simplicity, we set the ip range statically (should be a config option)
            ip_str = str(ip)
            # is there any current reservation for that lease?
            records = self.ip_schedule.find(resource_id=ip_str, start_time=datetime.utcnow())
            if not records: # empty list
                valuedicts.append(self._convert_reservation_to_dict(ip_str))
            else: # there should only be one record
                valuedicts.append(self._convert_reservation_to_dict(ip_str, records[0]))
        return valuedicts
    
    def reserve_lease(self, ip_str, slice_name, owner_uuid, owner_email=None, end_time=None):
        end_time = self._revise_end_time(end_time, ip_str)
        reservation = None
        try:
            reservation = self.ip_schedule.reserve(
                resource_id=ip_str,
                resource_spec={"additional_information" : "unused"},
                slice_id=slice_name,
                user_id=owner_email,
                end_time=end_time)
        except sex.ScheduleOverbookingError, e:
            raise DHCPLeaseAlreadyTaken(ip_str)
        return self._convert_reservation_to_dict(ip_str, reservation)
    
    def extend_lease(self, ip_str, end_time=None):
        reservations = self.ip_schedule.find(resource_id=ip_str, start_time=datetime.utcnow())
        if len(reservations) != 1:
            raise DHCPLeaseNotFound(ip_str)
        end_time = self._revise_end_time(end_time, ip_str)
        result = self.ip_schedule.update(reservations[0].reservation_id, end_time=end_time)
        return self._convert_reservation_to_dict(ip_str, result)
    
    def leases_in_slice(self, slice_name):
        """Finds only current leases for the given slice name."""
        reservations = self.ip_schedule.find(slice_id=slice_name, start_time=datetime.utcnow())
        return [self._convert_reservation_to_dict(r['resource_id'], r) for r in reservations]
        
    
    def free_lease(self, ip_str):
        reservations = self.ip_schedule.find(resource_id=ip_str, start_time=datetime.utcnow())
        if len(reservations) != 1:
            raise DHCPLeaseNotFound(ip_str)
        self.ip_schedule.cancel(reservations[0].reservation_id)
        return None
        
    @worker.outsideprocess
    def expire_leases(self, params):
        # expire the leases of the last 100 days
        reservations = self.ip_schedule.find(start_time=datetime.utcnow()-timedelta(-100), end_time=datetime.utcnow())
        # the returned reservations could still be running as of now
        for reservation in reservations:
            if reservation.end_time < datetime.utcnow():
                logger.info("Removing expired DHCP lease: %s" % (lease.ip_str,))
        return

    def _revise_end_time(self, end_time, ip_str):
        """If {end_time} is none, the current time+{max_duration} is assumed."""
        max_end_time = datetime.utcnow() + timedelta(0, self.MAX_LEASE_DURATION)
        if end_time == None:
            end_time = max_end_time
        if (end_time > max_end_time):
            raise DHCPMaxLeaseDurationExceeded(ip_str)
        return end_time
    
    def _convert_reservation_to_dict(self, ip_str, reservation=None):
        """Returns the a value object to be returned to the delegate. If None is given, return a value object which is currently available."""
        if reservation is None: # empty list
            return {
                "ip_str" : ip_str,
                "available": True
            }
        else:
            return {
                "ip_str" : ip_str,
                "available" : False,
                "slice_name" : reservation.slice_id,
                "end_time" : reservation.end_time
            }
