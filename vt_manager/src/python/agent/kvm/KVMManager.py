# -*- coding: utf-8 -*-
'''
	@author: AIST

	KVM manager; handles KVM calls through libvirt library
'''
import libvirt
import time
import traceback
from threading import Lock
from kvm.provisioning.HdManager import HdManager
from utils.Logger import Logger

OXA_KVM_STOP_STEP_SECONDS = 6
OXA_KVM_STOP_MAX_SECONDS = 100
OXA_KVM_REBOOT_WAIT_TIME = 20
OXA_KVM_CREATE_WAIT_TIME = 2
OXA_KVM_MAX_DUPLICATED_NAME_VMS = 999999

class KVMManager(object):
	logger = Logger.getLogger()
	_mutex = Lock() 
	_kvmConnection = None  # NEVER CLOSE IT 
	_kvmConnectionRO = None  # Not really used 
	logger = Logger.getLogger()

	# Shell util
	@staticmethod
	def sanitize_arg(arg):
		return arg.replace('\\', '\\\\').replace('\'', '\\\'').replace(' ', '\ ') 
	
	@staticmethod
	def __getROConnection():
		# return libvirt.openReadOnly(None)
		return KVMManager.__getConnection()  # By-passed
	
	@staticmethod
	def __getConnection():
		with KVMManager._mutex:
			if KVMManager._kvmConnection is None:
				KVMManager._kvmConnection = libvirt.open(None)
			return KVMManager._kvmConnection
	
	@staticmethod
	def __getDomainByVmName(conn, name):
		return conn.lookupByName(name)	

	@staticmethod
	def __getDomainByVmUUID(conn, uuid):
		return conn.lookupByUUIDString(uuid)	

	# Monitoring	
	@staticmethod
	def isVmRunning(name):
		conn = KVMManager.__getROConnection() 
		try:
			dom = conn.lookupByName(name)	
			return dom.isActive()
		except Exception as e:
			KVMManager.logger.error(str(e))
			KVMManager.logger.error(traceback.format_exc())
			return False

	@staticmethod
	def isVmRunningByUUID(uuid):
		conn = KVMManager.__getROConnection() 
		try:
			dom = conn.lookupByUUIDString(uuid)	
			return dom.isActive()
		except Exception as e:
			KVMManager.logger.error(str(e))
			KVMManager.logger.error(traceback.format_exc())
			return False

	@staticmethod
	def retrieveActiveDomainsByUUID():
		conn = KVMManager.__getROConnection()
		domainIds = conn.listDomainsID()
		doms = list()

		for dId in domainIds:
			# Skip domain0
			if dId == 0:
				continue
	
			domain = conn.lookupByID(dId)
			doms.append((domain.UUIDString(), domain.name()))

		return doms 

	@staticmethod
	def __findAliasForDuplicatedVmName(vm):
		# Duplicated VM name; find new temporal alias
		for i in range(OXA_KVM_MAX_DUPLICATED_NAME_VMS):
			newVmName = vm.name + "_" + str(i)
			if not KVMManager.isVmRunning(vm.name + "_" + str(i)):
				KVMManager.logger.debug("using newVmName = " + newVmName)
				return str(newVmName)
		
		Exception("Could not generate an alias for a duplicated vm name.")

	# Provisioning routines
	@staticmethod
	def startDomain(vm):
		KVMManager.logger.info('startDomain ' + vm.name)
		# Getting connection
		conn = KVMManager.__getConnection()

		with open(HdManager.getConfigFilePath(vm), 'r') as openConfig: 
			xmlConf = openConfig.read()

		if KVMManager.isVmRunning(vm.name) and not KVMManager.isVmRunningByUUID(vm.uuid):
			# Duplicated name; trying to find an Alias
			newVmName = KVMManager.__findAliasForDuplicatedVmName(vm)
			xmlConf.replace("<name>"+ vm.name + "<\/name>", "<name>"+ newVmName + "<\/name>", 1)
			KVMManager.logger.warn("duplicate VM name, change VM name from " + vm.name
				+ " to " + newVmName)
		
		try:
			# Try first using libvirt call
			KVMManager.logger.info('creating vm using python-libvirt methods')
			KVMManager.logger.info(xmlConf)
			conn.createXML(xmlConf, 0)
			KVMManager.logger.info(KVMManager.sanitize_arg(HdManager.getConfigFilePath(vm)))
			KVMManager.logger.info('created vm')
			# raise Exception("Skip") #otherwise stop is ridiculously slow
		except Exception as e:
			KVMManager.logger.error(str(e))
			KVMManager.logger.error(traceback.format_exc())
			raise Exception(e)

		time.sleep(OXA_KVM_CREATE_WAIT_TIME)

		if not KVMManager.isVmRunningByUUID(vm.uuid):
			# Complete with other types of exceptions
			raise Exception("Could not start VM, abort")
		
		return

	@staticmethod
	def stopDomain(vm):
		# If is not running skip
		if not KVMManager.isVmRunningByUUID(vm.uuid):
			return	

		# dom = KVMManager.__getDomainByVmName(KVMManager.__getConnection(),vm.name)
		dom = KVMManager.__getDomainByVmUUID(KVMManager.__getConnection(), vm.uuid)
		
		# Attempt to be smart and let S.O. halt himself
		dom.shutdown()	
		
		waitTime = 0
		while (waitTime < OXA_KVM_STOP_MAX_SECONDS) :
			if not KVMManager.isVmRunningByUUID(vm.uuid):
				break
			waitTime += OXA_KVM_STOP_STEP_SECONDS
			time.sleep(OXA_KVM_STOP_STEP_SECONDS)

		# Let's behave impatiently
		dom.destroy()
		
		time.sleep(OXA_KVM_REBOOT_WAIT_TIME)
	
		if KVMManager.isVmRunningByUUID(vm.uuid):
			raise Exception("Could not stop domain")
		return

	@staticmethod
	def rebootDomain(vm):
		# dom = KVMManager.__getDomainByVmName(KVMManager.__getConnection(),vm.name)
		dom = KVMManager.__getDomainByVmUUID(KVMManager.__getConnection(), vm.uuid)
		dom.reboot(0)
		time.sleep(OXA_KVM_REBOOT_WAIT_TIME)
		if not KVMManager.isVmRunningByUUID(vm.uuid):
			raise Exception("Could not reboot domain (maybe rebooted before MINIMUM_RESTART_TIME?). Domain will remain in stop state")
		return

	''' XXX: To be implemented '''
		
	@staticmethod
	def pauseDomain(vm):
		# XXX		
		raise Exception("Not implemented")
		
	@staticmethod
	def resumeDomain(vm):
		# XXX
		raise Exception("Not implemented")	
	
