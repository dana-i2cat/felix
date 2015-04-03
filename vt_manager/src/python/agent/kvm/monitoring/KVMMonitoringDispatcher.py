# -*- coding: utf-8 -*-
'''
	@author: AIST

	KVMMonitoringDispatcher routines
'''
from kvm.KVMManager import KVMManager
from monitoring.MonitoringDispatcher import MonitoringDispatcher
from communications.XmlRpcClient import XmlRpcClient
from utils.Logger import Logger

class KVMMonitoringDispatcher(MonitoringDispatcher):
	
	logger = Logger.getLogger()
	
	# #Monitoring routines
	@staticmethod
	def listActiveVMs(vmid, server):
		try:		
			doms = KVMManager.retrieveActiveDomainsByUUID()
			XmlRpcClient.sendAsyncMonitoringActiveVMsInfo(vmid, "SUCCESS", doms, server)
		except Exception as e:
			# Send async notification
			XmlRpcClient.sendAsyncMonitoringActionStatus(vmid, "FAILED", str(e))
			KVMMonitoringDispatcher.logger.error(str(e))
		return
		
