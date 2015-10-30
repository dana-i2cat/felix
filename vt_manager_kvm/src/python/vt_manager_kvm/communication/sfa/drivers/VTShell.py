from vt_manager_kvm.models.VirtualMachine import VirtualMachine
from vt_manager_kvm.models.VTServer import VTServer
from vt_manager_kvm.models.Action import Action
from vt_manager_kvm.models.expiring_components import ExpiringComponents

from vt_manager_kvm.communication.sfa.util.xrn import Xrn, hrn_to_urn, get_leaf

from vt_manager_kvm.controller.drivers.VTDriver import VTDriver
from vt_manager_kvm.communication.sfa.vm_utils.VMSfaManager import VMSfaManager
from vt_manager_kvm.communication.sfa.vm_utils.SfaCommunicator import SfaCommunicator
from vt_manager_kvm.utils.ServiceThread import ServiceThread
from vt_manager_kvm.utils.SyncThread import SyncThread

import threading
import time
import random

from vt_manager_kvm.controller.dispatchers.xmlrpc.ProvisioningDispatcher import ProvisioningDispatcher
from vt_manager_kvm.utils.UrlUtils import UrlUtils
#XXX:To implement SfaCommunicator for a better use of SFA CreateSliver and Start/Stop/Delete/Update slice
#from vt_manager_kvm.common.middleware.thread_local import thread_locals, push
#from multiprocessing import Pipe

class VTShell:

        def __init__(self):
                pass

	def GetNodes(self,slice=None,authority=None,uuid=None):
		servers = VTServer.objects.all()
		if uuid:
			for server in servers:
				if str(server.uuid) == str(uuid):
					return server
			return None
		if not slice: 
		    return servers
		else:
		    slice_servers = list()
		    for server in servers:
                        if slice == None:
			    vms = server.getChildObject().getVMs(projectName = authority)
                        elif authority == None:
                            vms = server.getChildObject().getVMs(sliceName=slice)
                        else:
                            vms = server.getChildObject().getVMs(sliceName=slice, projectName = authority)
                        if vms:
			    slice_servers.append(server)
                    return slice_servers

	def GetSlice(self,slicename,authority):

		name = slicename # or uuid...
		servers = self.GetNodes()
		slices = dict()
		List = list()
		for server in servers:
			child_server = server.getChildObject()
                        if not authority:
      				vms = child_server.getVMs(sliceName=name)
                        elif not slicename:
                                vms = child_server.getVMs(projectName = authority)
                        else:
                                vms = child_server.getVMs(sliceName=name, projectName = authority)
			for vm in vms:
                                ip = self.get_ip_from_vm(vm)
                                state = vm.state
                                if str(vm.state) == "unknown":
                                    state = "ongoing"
				List.append({'vm-name':vm.name,'vm-state':state,'vm-id':vm.id, 'vm-ip':ip, 'node-id':server.uuid, 'node-name':server.name})
			        	
		slices['vms'] = List
		return slices	

	def StartSlice(self,server_uuid,vm_id):
                vm = VirtualMachine.objects.get(id=vm_id)
                if "stopped" in vm.state:
		        return self.__crudVM(server_uuid,vm_id,Action.PROVISIONING_VM_START_TYPE)

	def StopSlice(self,server_uuid,vm_id):
		return self.__crudVM(server_uuid,vm_id,Action.PROVISIONING_VM_STOP_TYPE)
	
	def RebootSlice(self,server_uuid,vm_id):
                return self.__crudVM(server_uuid,vm_id,Action.PROVISIONING_VM_REBOOT_TYPE)

	def DeleteSlice(self,server_uuid,vm_id):
                return self.__crudVM(server_uuid,vm_id,Action.PROVISIONING_VM_DELETE_TYPE)

	def __crudVM(self,server_uuid,vm_id,action):
		try:
			VTDriver.PropagateActionToProvisioningDispatcher(vm_id, server_uuid, action)
		except Exception as e:	
			raise e
		return 1

	def CreateSliver(self,vm_params,projectName,sliceName,expiration):
		#processes = list()
                self.modify_sliver_names(vm_params,projectName, sliceName)
		provisioningRSpecs = VMSfaManager.getActionInstance(vm_params,projectName,sliceName)
		for provisioningRSpec in provisioningRSpecs:
		    #waiter,event = Pipe()
		    #process = SfaCommunicator(provisioningRSpec.action[0].id,event,provisioningRSpec)
		    #processes.append(process)
		    #process.start()
                    with threading.Lock():
                        SyncThread.startMethodAndJoin(ProvisioningDispatcher.processProvisioning,provisioningRSpec,'SFA.OCF.VTM') #UrlUtils.getOwnCallbackURL())
                        
                    if expiration:
                        ExpiringComponents.objects.create(slice=sliceName, authority=projectName, expires=expiration).save()
                         
		#waiter.recv()
		return 1
 
	def GetSlices(server_id,user=None):
		#TODO: Get all the vms from a node and from an specific user
		pass

        def convert_to_uuid(self,requested_attributes):
                for slivers in requested_attributes:
                        servers = VTServer.objects.filter(name=get_leaf(slivers['component_id']))
		        slivers['component_id'] = servers[0].uuid
                return requested_attributes
      
        def get_ip_from_vm(self, vm=None, vm_name=None, slice_name=None, project=None):
                if not vm: 
                        vms = VirtualMachine.objects.filter(name=vm_name, sliceName=slice_name, projectName=project)
                        for vm in vms:
                                
                                if vm.name == vm_name:
                                        break;
                        return "None" 
                ifaces = vm.getNetworkInterfaces()
                for iface in ifaces:
                        if iface.isMgmt:
                            return iface.ip4s.all()[0].ip #IP
                return "None" 

        def modify_sliver_names(self, vm_params,authority, slice_name):
                vms = VirtualMachine.objects.filter(sliceName=slice_name, projectName=authority)
                names = list()
                for vm in vms:
                    names.append(vm.name)
                for sliver in vm_params:
                    for vm in sliver['slivers']:
                         if vm['name'] in names:
                             vm['name'] = vm['name'] + str(random.randint(0,999))
                                  
