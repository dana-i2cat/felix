# -*- coding: utf-8 -*-
'''
	@author: AIST

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
