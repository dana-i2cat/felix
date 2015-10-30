from django.core.mail import send_mail
from django.conf import settings
from vt_manager_kvm.models import ExpiringComponents
from vt_manager_kvm.models.VirtualMachine import VirtualMachine
from vt_manager_kvm.communication.geni.v3.configurators.handlerconfigurator import HandlerConfigurator
from am.geniutils.src.xrn.xrn import hrn_to_urn
from datetime import datetime
import re
import threading
import time


class BackgroundVMEXpirationMonitoring(threading.Thread):
      
    period = 3600  #seconds
   
    def __init__(self):
        threading.Thread.__init__(self)
        self.period = 900
        self.vt_driver = HandlerConfigurator.get_vt_am_driver()
        
    def monitor(self):
        self.start()
     
    def run(self):
        while True:
            print "Background VM Expiration Thread starting..."
            expirations = ExpiringComponents.objects.all()
            try:
                for e in expirations:
                    exp_date = re.sub(r'[\+].+', "", e.expires)
                    exp_date = exp_date.replace("Z", "").replace("T", " ")
                    try:
                        exp_time = datetime.strptime(exp_date, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        exp_time = datetime.strptime(exp_date, '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.utcnow()
                    time_to_expire = current_time - exp_time
                    if exp_time < current_time:
                        vms = VirtualMachine.objects.filter(sliceName=e.slice, projectName=e.authority)
                        for vm in vms:
                            try:
                                sliver_urn = hrn_to_urn(e.slice + "." + vm.name, "sliver")
                                print "VM (urn=%s) has expired on time=%s. Proceeding to its deletion" % \
                                        (sliver_urn, e.expires)
                                self.vt_driver.delete_vm(sliver_urn)
                            except:
                                pass
                        e.delete()
                    # If one hour or less is left for expiring, notify it to experimenter
                    elif time_to_expire.days == 0 and time_to_expire.seconds <= 60*60:
                        vms = VirtualMachine.objects.filter(sliceName=e.slice, projectName=e.authority)
                        slice_urn = hrn_to_urn(e.slice, "slice")
                        for vm in vms:
                            sliver_urn = hrn_to_urn(e.slice + "." + vm.name, "sliver")
                            send_mail(
                                settings.ISLAND_NAME + ": sliver expiring at %s island" % settings.ISLAND_NAME,
                                "Sliver %s from slice %s, is going to expire in approximately 1 hour.\n\nPlease renew it or delete / let it expire if you are not using it anymore." % (sliver_urn, slice_urn),
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                # TODO Should be set to the maintainer's e-mail (maybe getting that from creds?)
                                recipient_list=[settings.ROOT_EMAIL],
                            )
            except Exception as e:
                print "Expiratio Monitoring failed, cause:", str(e)
            
            time.sleep(self.period)
