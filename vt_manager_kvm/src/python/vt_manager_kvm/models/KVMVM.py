# -*- coding: utf-8 -*-
# Copyright (C) 2015
# National Institute of Advanced Industrial Science and Technology
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

from django.db import models
from django.contrib import auth
from datetime import datetime
from vt_manager_kvm.models.faults import *
import re
import inspect 
from vt_manager_kvm.models.VirtualMachine import VirtualMachine
from vt_manager_kvm.utils.MutexStore import MutexStore
from vt_manager_kvm.models.utils.Choices import VirtTechClass


''' Choices  and constants '''
#HD setup type
HD_SETUP_TYPE_FILE_IMAGE = "file-image"
HD_SETUP_TYPE_CHOICES = (
       	(HD_SETUP_TYPE_FILE_IMAGE, 'File image'),
)

#Virtualization type
VIRTUALIZATION_SETUP_TYPE_HAV = "hardware-assisted-virtualization"
VIRTUALIZATION_SETUP_TYPE = (
       	(VIRTUALIZATION_SETUP_TYPE_HAV, 'Hardware-assisted virtualization'),
)


IMAGE_CONFIGURATORS = {
			'default/default.tar.gz':'',
                        'legacy/legacy.tar.gz':'',
			'irati/irati.img':'IratiDebianVMConfigurator',
			'spirentSTCVM/spirentSTCVM.img':'SpirentCentOSVMConfigurator',
                        'debian7/debian7.img': 'DebianWheezyVMConfigurator',
			}
	

'''
Ugly wrappers due to Django limitation on the validators
'''
def validateHdSetupWrapper(param):
	return KVMVM.validateHdSetupType(param)
def validateVirtualizationSetupType(param):
	return KVMVM.validateHdSetupType(param)


	
class KVMVM(VirtualMachine):

	class Meta:
		"""Meta Class for your model."""
		app_label = 'vt_manager_kvm'

	"""KVM VM data model class"""
	#server = models.OneToOneField('KVMServer', blank = False, null = False, editable = False, verbose_name = "KVM server")

	hdSetupType = models.CharField(max_length = 1024, default="",validators=[validateHdSetupWrapper])
	hdOriginPath = models.CharField(max_length = 1024, default="")
	virtualizationSetupType = models.CharField(max_length = 1024, default="",validators=[validateVirtualizationSetupType])
	virttech = VirtTechClass.VIRT_TECH_TYPE_KVM


	@staticmethod
	def constructor(name,uuid,projectId,projectName,sliceId,sliceName,osType,osVersion,osDist,memory,discSpaceGB,numberOfCPUs,callBackUrl,interfaces,hdSetupType,hdOriginPath,virtSetupType,save=True):
		self =  KVMVM()
		try:
			#Set common fields
			self.setName(name)
			self.setUUID(uuid)
			self.setProjectId(projectId)
			self.setProjectName(projectName)
			self.setSliceId(sliceId)
			self.setSliceName(sliceName)
			self.setOSType(osType)
			self.setOSVersion(osVersion)
			self.setOSDistribution(osDist)
			self.setMemory(memory)
			self.setDiscSpaceGB(discSpaceGB)
			self.setNumberOfCPUs(numberOfCPUs)
			self.setCallBackURL(callBackUrl)
			self.setState(self.UNKNOWN_STATE)
			for interface in interfaces:
				self.networkInterfaces.add(interface)
			#self.server = server
	
			#KVM parameters
			self.hdSetupType =hdSetupType
			self.hdOriginPath = hdOriginPath
			self.virtualizationSetupType = virtSetupType
	
			self.doSave = save
			if save:	
				self.save()
		except Exception as e:
			#self.delete()
			print e
			raise e

		return self	
	
	'''Destructor'''
	def destroy(self):	
		with MutexStore.getObjectLock(self.getLockIdentifier()):
			#destroy interfaces
			for inter in self.networkInterfaces.all():
				inter.destroy()
			self.delete()
	
	''' Getters and setters '''
	def getHdSetupType(self):
		return 	self.hdSetupType
	
	@staticmethod
	def validateHdSetupType(hdType):
		if hdType not in HD_SETUP_TYPE_CHOICES:
			raise Exception("Invalid HD Setup type")
			
	def setHdSetupType(self,hdType):
		KVMVM.validateHdSetupType(hdType)
		self.hdSetupType
		self.autoSave()

	def getHdOriginPath(self):
		return 	self.hdSetupType
	def setHdOriginPath(self,path):
		self.hdOriginPath = path
		self.autoSave()
	def getVirtualizationSetupType(self):
		return 	self.virtualizationSetupType
	@staticmethod
	def validateVirtualizationSetupType(self,vType):
		if vType not in VIRTUALIZATION_SETUP_TYPE:
			raise Exception("Invalid Virtualization Setup type")
			
	def setVirtualizationSetupType(self,vType):
		self.validateVirtualizationSetupType(vType)
		self.virtualizationSetupType = vType
		self.autoSave()



	''' Factories '''
	@staticmethod
	def create(name,uuid,projectId,projectName,sliceId,sliceName,osType,osVersion,osDist,memory,discSpaceGB,numberOfCPUs,callBackUrl,interfaces,hdSetupType,hdOriginPath,virtSetupType,save=True):
		return KVMVM.constructor(name,uuid,projectId,projectName,sliceId,sliceName,osType,osVersion,osDist,memory,discSpaceGB,numberOfCPUs,callBackUrl,interfaces,hdSetupType,hdOriginPath,virtSetupType,save)
