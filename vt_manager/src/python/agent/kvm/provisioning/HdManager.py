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
	Abstract class that handles Hd management routines.
'''

class HdManager(object):
	@staticmethod
	def __getHdManager(hdtype):
		#Import of Dispatchers must go here to avoid import circular dependency 		
		from kvm.provisioning.hdmanagers.FileHdManager import FileHdManager

		return FileHdManager

	##Public methods
	@staticmethod
	def getHdPath(vm):
		man = HdManager.__getHdManager("")		
		return man.getHdPath(vm)
	@staticmethod
	def getSwapPath(vm):
		man = HdManager.__getHdManager("")		
		return man.getSwapPath(vm)
	
	@staticmethod
	def getConfigFilePath(vm):
		man = HdManager.__getHdManager("")		
		return man.getConfigFilePath(vm)
	
	@staticmethod
	def clone(vm):
		man = HdManager.__getHdManager("")		
		return man.clone(vm)
	
	@staticmethod
	def mount(vm):
		man = HdManager.__getHdManager("")		
		return man.mount(vm)
	
	@staticmethod
	def umount(vm,path):
		man = HdManager.__getHdManager("")		
		return man.umount(path)
	
	@staticmethod
	def delete(vm):
		man = HdManager.__getHdManager("")		
		return man.delete(vm)

	#Hooks
	@staticmethod
	def startHook(vm):
		man = HdManager.__getHdManager("")		
		return man.startHook(vm)
	@staticmethod
	def stopHook(vm):
		man = HdManager.__getHdManager("")		
		return man.stopHook(vm)
	@staticmethod
	def rebootHook(vm):
		man = HdManager.__getHdManager("")		
		return man.rebootHook(vm)
