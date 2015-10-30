from django.http import *
import os, sys, logging
from vt_manager_kvm.models import *
from vt_manager_kvm.controller import *
from vt_manager_kvm.communication.utils.XmlHelper import *
from vt_manager_kvm.utils.ServiceThread import *
from vt_manager_kvm.common.rpc4django import rpcmethod
from vt_manager_kvm.common.rpc4django import *
from vt_manager_kvm.controller.dispatchers.xmlrpc.DispatcherLauncher import DispatcherLauncher
from vt_manager_kvm.utils.SyncThread import *


@rpcmethod(url_name="agent", signature=['string', 'string'])
def sendAsync(xml):
	logging.debug("sendAsync lauched")
	rspec = XmlHelper.parseXmlString(xml)
	ServiceThread.startMethodInNewThread(DispatcherLauncher.processXmlResponse ,rspec)
	#ServiceThread.startMethodInNewThread(ProvisioningResponseDispatcher.processResponse , rspec)
	return

@rpcmethod(ulr_name="agent", signature=['string', 'string'])
def sendSync(xml):
	logging.debug("sendSync lauched")
	rspec = XmlHelper.parseXmlString(xml)
	SyncThread.startMethodAndJoin(DispatcherLauncher.processXmlResponseSync, rspec)
	return

