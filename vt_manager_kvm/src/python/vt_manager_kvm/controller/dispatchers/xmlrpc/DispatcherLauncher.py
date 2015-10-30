from django.http import *                                                     
import os                                                                     
import sys                                                                    
from vt_manager_kvm.controller.dispatchers.xmlrpc.ProvisioningDispatcher import ProvisioningDispatcher
from vt_manager_kvm.controller.dispatchers.xmlrpc.ProvisioningResponseDispatcher import ProvisioningResponseDispatcher
from vt_manager_kvm.controller.dispatchers.xmlrpc.MonitoringResponseDispatcher import MonitoringResponseDispatcher
from vt_manager_kvm.controller.dispatchers.xmlrpc.InformationDispatcher import InformationDispatcher
from vt_manager_kvm.communication.utils import *                                  
from vt_manager_kvm.utils.ServiceThread import *                                      
from vt_manager_kvm.common.rpc4django import rpcmethod                                       
from vt_manager_kvm.common.rpc4django import *                                               
import threading                                                                             
import multiprocessing
#XXX: Sync Thread for VTPlanner
from vt_manager_kvm.utils.SyncThread import *
import logging

class DispatcherLauncher():
    logger = logging.getLogger("DispatcherLauncher")
    
    @staticmethod
    def processXmlResponse(rspec):
		if not rspec.response.provisioning == None:
			ServiceThread.startMethodInNewThread(ProvisioningResponseDispatcher.processResponse, rspec)
		if not rspec.response.monitoring == None:
			ServiceThread.startMethodInNewThread(MonitoringResponseDispatcher.processResponse, rspec)

    @staticmethod
    def processXmlQuery(rspec):
        #check if provisioning / monitoring / etc
        if not rspec.query.provisioning == None :
            DispatcherLauncher.logger.debug("XXX start provision thread")
            ServiceThread.startMethodInNewThread(ProvisioningDispatcher.processProvisioning,rspec.query.provisioning, threading.currentThread().callBackURL)
        else:
            DispatcherLauncher.logger.debug("XXX skip starting provision thread")
            pass
        return

    @staticmethod    
    def processXmlQuerySync(rspec,url=None):
	    #check if provisioning / monitoring / etc
	if threading.currentThread().callBackURL:
		url = threading.currentThread().callBackURL
        if not rspec.query.provisioning == None :
            status = SyncThread.startMethodAndJoin(ProvisioningDispatcher.processProvisioning, rspec.query.provisioning, url)
            return status

    @staticmethod
    def processInformation(remoteHashValue, projectUUID ,sliceUUID):
		return InformationDispatcher.listResources(remoteHashValue, projectUUID, sliceUUID)

    @staticmethod
    def processVMTemplatesInfo(serverUUID):
    #def processVMTemplatesInfo(serverUUID, callbackURL):
        #ServiceThread.startMethodInNewThread(InformationDispatcher.listVMTemplatesInfo, [serverUUID, callbackURL])
        
        #if not callbackURL and threading.currentThread().callBackURL:
        #    callbackURL = threading.currentThread().callBackURL
        #vm_templates = SyncThread.startMethodAndJoin(InformationDispatcher.listVMTemplatesInfo, serverUUID, callbackURL)
        #return vm_templates
        
        return InformationDispatcher.listVMTemplatesInfo(serverUUID)

