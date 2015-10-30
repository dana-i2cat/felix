from threading import Thread
import random
import logging
import traceback
import vt_manager_kvm.communication.utils.ZabbixHelper
from vt_manager_kvm.communication.XmlRpcClient import XmlRpcClient
from vt_manager_kvm.controller.monitoring.VMMonitor import VMMonitor
from vt_manager_kvm.communication.utils.ZabbixHelper import ZabbixHelper
from django.db import connection

'''
	author:msune
	Agent monitoring thread
'''

MONITORING_INTERVAL_FACTOR=0.0

class AgentMonitoringThread(Thread):
	logger = logging.getLogger("AgentMonitoringThread")

	__method = None
	__param = None

	#XXX: this is a temporary patch. Use agent proactive calls based on libvirt callback instead
	def periodicRefresh(self):
		#stateless peridoic refresh
		return random.random() > MONITORING_INTERVAL_FACTOR	
		
	'''
	Make sure Agent is up and running
	and updates status
	'''
		

	def __updateAgentStatus(self, server):
		try:
			print "Pinging Agent on server %s" % server.name
			XmlRpcClient.callRPCMethod(server.getAgentURL(),"ping", "hola")
			#Server is up
			print "Ping Agent on server %s was SUCCESSFUL!" % server.name
			ZabbixHelper.sendAgentStatus(server, True)
			if self.periodicRefresh() or server.available == False:
				#Call it 
				VMMonitor.sendUpdateVMs(server)
			
				if server.available == False:
					print " set %s as available" % server.name
					server.setAvailable(True)
					server.save()
		except Exception as e:
			#If fails for some reason mark as unreachable
			print "Could not reach server %s. Will be set as unavailable " % str(server.name)
			print e
			print traceback.format_exc()
			server.setAvailable(False)
			server.save()
			ZabbixHelper.sendAgentStatus(server, False)
		finally:
			connection.close()
		return

	@staticmethod
	def monitorAgentInNewThread(param):
		thread = AgentMonitoringThread()	
		thread.startMethod(param)
		return thread

	def startMethod(self,param):
		self.__method = self.__updateAgentStatus 
		self.__param = param
		self.start()

	def run(self):	
		self.__method(self.__param)			
