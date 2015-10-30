from vt_manager_kvm.controller.drivers.VTDriver import VTDriver
from vt_manager_kvm.models.KVMServer import KVMServer
from vt_manager_kvm.models.KVMVM import KVMVM
from vt_manager_kvm.models.VTServer import VTServer
from vt_manager_kvm.utils.HttpUtils import HttpUtils
import threading
import logging

class KVMDriver(VTDriver):
	logger = logging.getLogger("KVMDriver")

#	def __init__(self):
#		self.ServerClass = eval('KVMServer') 
#		self.VMclass = eval('KVMVM') 


	@staticmethod
	def getInstance():
		return KVMDriver()

	def deleteVM(self, vm):
		KVMDriver.logger.debug("deleteVM start")
		try:
			vm.Server.get().deleteVM(vm)
		except:
			raise	

	def getServerAndCreateVM(self,action):
		try: 
			Server = KVMServer.objects.get(uuid = action.server.uuid )
			VMmodel = Server.createVM(*KVMDriver.kvmVMtoModel(action.server.virtual_machines[0],threading.currentThread().callBackURL, save = True))
			return Server, VMmodel
		except Exception as e:
			raise e
	
	@staticmethod
	def createOrUpdateServerFromPOST(request, instance):
		#return KVMServer.constructor(server.getName(),server.getOSType(),server.getOSDistribution(),server.getOSVersion(),server.getAgentURL(),save=True)
		server = KVMServer.objects.get(uuid = instance.getUUID())
		if server:
			return server.updateServer(HttpUtils.getFieldInPost(request,VTServer, "name"),
				HttpUtils.getFieldInPost(request,VTServer, "operatingSystemType"),
				HttpUtils.getFieldInPost(request,VTServer, "operatingSystemDistribution"),
				HttpUtils.getFieldInPost(request,VTServer, "operatingSystemVersion"),
				HttpUtils.getFieldInPost(request,VTServer, "numberOfCPUs"),
				HttpUtils.getFieldInPost(request,VTServer, "CPUFrequency"),
				HttpUtils.getFieldInPost(request,VTServer, "memory"),
				HttpUtils.getFieldInPost(request,VTServer, "discSpaceGB"),
				HttpUtils.getFieldInPost(request,VTServer, "agentURL"),
				save=True)
		else:
			return KVMServer.constructor(HttpUtils.getFieldInPost(request,VTServer, "name"),
							HttpUtils.getFieldInPost(request,VTServer, "operatingSystemType"),
							HttpUtils.getFieldInPost(request,VTServer, "operatingSystemDistribution"),
							HttpUtils.getFieldInPost(request,VTServer, "operatingSystemVersion"),
							HttpUtils.getFieldInPost(request,VTServer, "numberOfCPUs"),
							HttpUtils.getFieldInPost(request,VTServer, "CPUFrequency"),
							HttpUtils.getFieldInPost(request,VTServer, "memory"),
							HttpUtils.getFieldInPost(request,VTServer, "discSpaceGB"),
							HttpUtils.getFieldInPost(request,VTServer, "agentURL"),
							save=True)
	
	def crudServerFromInstance(self,instance):
		server = KVMServer.objects.filter(uuid = instance.getUUID())
		if len(server)==1:
			server = server[0]
			return server.updateServer(instance.getName(),
						instance.getOSType(),
						instance.getOSDistribution(),
						instance.getOSVersion(),
						instance.getNumberOfCPUs(),
						instance.getCPUFrequency(),
						instance.getMemory(),
						instance.getDiscSpaceGB(),
						instance.getAgentURL(),
						instance.getAgentPassword(),
						save = True)
		elif len(server)==0:
			return KVMServer.constructor(instance.getName(),
								instance.getOSType(),
								instance.getOSDistribution(),
								instance.getOSVersion(),
								instance.getNumberOfCPUs(),
								instance.getCPUFrequency(),
								instance.getMemory(),
								instance.getDiscSpaceGB(),
								instance.getAgentURL(),
								instance.getAgentPassword(),
								save=True)
		else:
			raise Exception("Trying to create a server failed")

	@staticmethod
	def kvmVMtoModel(VMxmlClass, callBackURL, save):
		name = VMxmlClass.name
		uuid = VMxmlClass.uuid
		projectId = VMxmlClass.project_id
		projectName = VMxmlClass.project_name
		sliceId = VMxmlClass.slice_id
		sliceName = VMxmlClass.slice_name
		osType = VMxmlClass.operating_system_type
		osVersion = VMxmlClass.operating_system_version
		osDist = VMxmlClass.operating_system_distribution
		memory = VMxmlClass.xen_configuration.memory_mb
		# XXX
		callBackUrl = callBackURL
		hdSetupType = VMxmlClass.xen_configuration.hd_setup_type
		hdOriginPath = VMxmlClass.xen_configuration.hd_origin_path
		virtSetupType = VMxmlClass.xen_configuration.virtualization_setup_type
		return name,uuid,projectId,projectName,sliceId,sliceName,osType,osVersion,osDist,memory,None,None,callBackUrl,hdSetupType,hdOriginPath,virtSetupType,save
