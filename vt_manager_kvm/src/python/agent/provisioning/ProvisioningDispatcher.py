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
	
'''
	Provisioning dispatcher. Selects appropiate Driver for VT tech
'''

import threading

from communications.XmlRpcClient import XmlRpcClient
from utils.VmMutexStore import VmMutexStore
from utils.Logger import Logger

class ProvisioningDispatcher: 
	
	logger = Logger.getLogger()

	@staticmethod
	def __getProvisioningDispatcher(vtype):

		#Import of Dispatchers must go here to avoid import circular dependecy 		
		from xen.provisioning.XenProvisioningDispatcher import XenProvisioningDispatcher
		from kvm.provisioning.KVMProvisioningDispatcher import KVMProvisioningDispatcher

		if vtype == "xen": 
			return XenProvisioningDispatcher 
		elif vtype == "kvm": 
			return KVMProvisioningDispatcher 
		else:
			raise Exception("Virtualization type not supported by the agent")	
	
	@staticmethod
	def __dispatchAction(dispatcher,action,vm):
		#Inventory
		if action.type_ == "create":
			ProvisioningDispatcher.logger.debug("XXX create called")
			return dispatcher.createVMfromImage(action.id,vm)
		if action.type_ == "modify" :
			ProvisioningDispatcher.logger.debug("XXX modify called")
			return dispatcher.modifyVM(action.id,vm)
		if action.type_ == "delete" :
			ProvisioningDispatcher.logger.debug("XXX delete called")
			return dispatcher.deleteVM(action.id,vm)

		#Scheduling 
		if action.type_ == "start":
			ProvisioningDispatcher.logger.debug("XXX start called")
			return dispatcher.startVM(action.id,vm)
		if action.type_ == "reboot" :
			ProvisioningDispatcher.logger.debug("XXX reboot called")
			return dispatcher.rebootVM(action.id,vm)
		if action.type_ == "stop" :
			ProvisioningDispatcher.logger.debug("XXX stop called")
			return dispatcher.stopVM(action.id,vm)
		if action.type_ == "hardStop" :
			ProvisioningDispatcher.logger.debug("XXX hardStop called")
			return dispatcher.hardStopVM(action.id,vm)
		raise Exception("Unknown action type")


	@staticmethod
	def processProvisioning(provisioning):
		for action in provisioning.action:
			vm = action.server.virtual_machines[0]
			try:
				dispatcher = ProvisioningDispatcher.__getProvisioningDispatcher(vm.virtualization_type)	
			except Exception as e:
				XmlRpcClient.sendAsyncProvisioningActionStatus(action.id,"FAILED",str(e))
				ProvisioningDispatcher.logger.error(str(e))	
				return

			try:
				#Acquire VM lock
				VmMutexStore.lock(vm)
				#Send async notification
				XmlRpcClient.sendAsyncProvisioningActionStatus(action.id,"ONGOING","")
	
				ProvisioningDispatcher.__dispatchAction(dispatcher,action,vm)	
			except Exception as e:
				ProvisioningDispatcher.logger.error(str(e))
				raise e
			finally:
				#Release VM lock
				VmMutexStore.unlock(vm)


	##Abstract methods definition for ProvisioningDispatchers
	#Inventory
	@staticmethod
	def createVMfromImage(vmid,vm):
		raise Exception("Abstract method cannot be called")	
	@staticmethod
	def modifyVM(vmid,vm):
		raise Exception("Abstract method cannot be called")
	@staticmethod
	def deleteVM(vmid,vm):
		raise Exception("Abstract method cannot be called")	
	
	#Scheduling
	@staticmethod
	def startVM(vmid,vm):
		raise Exception("Abstract method cannot be called")	
	@staticmethod
	def rebootVM(vmid,vm):
		raise Exception("Abstract method cannot be called")	
	@staticmethod
	def stopVM(vmid,vm):
		raise Exception("Abstract method cannot be called")	
	@staticmethod
	def hardStopVM(vmid,vm):
		raise Exception("Abstract method cannot be called")	

