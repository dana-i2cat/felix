# -*- coding: utf-8 -*-

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
	KVMProvisioningDispatcher routines
'''
from kvm.provisioning.HdManager import HdManager
from kvm.KVMManager import KVMManager
from kvm.provisioning.VMConfigurator import VMConfigurator
from provisioning.ProvisioningDispatcher import ProvisioningDispatcher
from communications.XmlRpcClient import XmlRpcClient
from utils.Logger import Logger
from utils.AgentExceptions import *
import traceback

class KVMProvisioningDispatcher(ProvisioningDispatcher):
	logger = Logger.getLogger()

	# #Inventory routines
	@staticmethod
	def createVMfromImage(vmid, vm):
		KVMProvisioningDispatcher.logger.info("XXX createVMfromImage start")
		pathToMountPoint = ""	
		KVMProvisioningDispatcher.logger.info("Initiating creation process for VM: " + vm.name
											+ " under project: " + vm.project_id
											+ " and slice: " + vm.slice_id)
		try:
			# Clone HD
			HdManager.clone(vm)
			KVMProvisioningDispatcher.logger.debug("HD cloned successfully...")
			
			# Mount copy
			pathToMountPoint = HdManager.mount(vm)
			KVMProvisioningDispatcher.logger.debug("Mounting at: " + pathToMountPoint)
			KVMProvisioningDispatcher.logger.debug("HD mounted successfully...")
			
			# Configure VM OS
			VMConfigurator.configureVmDisk(vm, pathToMountPoint)

			# Umount copy
			HdManager.umount(vm, pathToMountPoint)
			KVMProvisioningDispatcher.logger.debug("HD unmounted successfully...")
	
			# Synthesize config file
			VMConfigurator.createVmConfigurationFile(vm)
			KVMProvisioningDispatcher.logger.debug("KVM configuration file created successfully...")
			
			KVMProvisioningDispatcher.logger.info("Creation of VM " + vm.name + " has been successful!!")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			KVMProvisioningDispatcher.logger.error(traceback.format_exc())
			# Send async notification
			try:
				HdManager.umount(vm, pathToMountPoint)
			except:
				pass
			try:
				# Delete VM disc and conf file if the error is not due because
				# the VM already exists
				if not isinstance(e, VMalreadyExists):
					KVMProvisioningDispatcher.deleteVM(vmid, vm)
			except:
				pass
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		KVMProvisioningDispatcher.logger.info("XXX createVMfromImage end")
		return

	@staticmethod
	def modifyVM(vmid, vm):
		# Check existence of VM
		raise Exception("Not implemented")

	@staticmethod
	def deleteVM(vmid, vm):
		try:
			try:
				# if it wasn't stopped, do it
				KVMManager.stopDomain(vm)	
			except Exception as e:
				pass
			
			# Trigger Hd Deletion in Remote	
			HdManager.delete(vm)	

			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			KVMProvisioningDispatcher.logger.exception("XXX")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		return
	
	# #Scheduling routines
	@staticmethod
	def startVM(vmid, vm):
		KVMProvisioningDispatcher.logger.info("XXX startVM start")
		try:
			# Trigger	
			HdManager.startHook(vm)	
			KVMManager.startDomain(vm)
	
			KVMProvisioningDispatcher.logger.info("VM named " + vm.name + " has been started.")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		KVMProvisioningDispatcher.logger.info("XXX startVM end")
		return

	@staticmethod
	def rebootVM(vmid, vm):
		try:
			# Just try to reboot
			HdManager.rebootHook(vm)
			KVMManager.rebootDomain(vm)
	
			KVMProvisioningDispatcher.logger.info("VM named " + vm.name + " has been rebooted.")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		return

	@staticmethod
	def stopVM(vmid, vm):
		try:
			# Just try to stop
			KVMManager.stopDomain(vm)
	
			KVMProvisioningDispatcher.logger.info("VM named " + vm.name + " has been stopped.")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		return

	@staticmethod
	def hardStopVM(vmid, vm):
		try:
			# First stop domain
			KVMManager.stopDomain(vm)	
			HdManager.stopHook(vm)	
		
			KVMProvisioningDispatcher.logger.info("VM named " + vm.name + " has been stopped.")
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "SUCCESS", "")
		except Exception as e:
			KVMProvisioningDispatcher.logger.error(str(e))
			# Send async notification
			XmlRpcClient.sendAsyncProvisioningActionStatus(vmid, "FAILED", str(e))
		return

