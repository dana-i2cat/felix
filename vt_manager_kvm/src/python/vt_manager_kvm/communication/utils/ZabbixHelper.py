# -*- coding: utf-8 -*-
'''
Created on 2015/04/17
@author: 2015 AIST
'''
import time
from django.conf import settings
from zbxsend import Metric, send_to_zabbix
import logging
import json 
from vt_manager_kvm.communication.geni.v3.configurators.handlerconfigurator import HandlerConfigurator

class ZabbixHelper():
	logger = logging.getLogger("ZabbixHelper")

	@staticmethod
	def sendAgentStatus(server, available):
		if available == True:
			status = 1 # UP
		else:
			status = 2 # DOWN
		timestamp = int(time.time())
		driver = HandlerConfigurator.get_vt_am_driver()
		server_urn = driver.generate_component_id(server)
		itemname = settings.ZBX_ITEM_HOSTSTATUS + '[' + str(server_urn) + ']'
		metric = Metric(server.name, str(itemname), status, timestamp)
		ZabbixHelper.sendZabbix(metric)
		return

	@staticmethod
	def sendVMDiscovery(server, vms):
		timestamp = int(time.time())
		discoveryList = []
		for vm in vms:
			discovery = {"{#USERVM.NAME}": vm.name}
			discoveryList.append(discovery)
		tmpobj = {"data": discoveryList}
		discoveryStr = json.dumps(tmpobj)
		metric = Metric(server.name, settings.ZBX_ITEM_DISCOVERY_USERVM,
					 str(discoveryStr), timestamp)
		ZabbixHelper.sendZabbix(metric)
		return

	@staticmethod
	def sendVMStatusDiscovery(vms):
		timestamp = int(time.time())
		driver = HandlerConfigurator.get_vt_am_driver()
		for vm in vms:
			discoveryList = []
			vm_urn = driver.generate_sliver_urn(vm)
			discovery = {"{#USERVM.URN}": vm_urn}
			discoveryList.append(discovery)
			tmpobj = {"data": discoveryList}
			discoveryStr = json.dumps(tmpobj)
			metric = Metric(vm.name, settings.ZBX_ITEM_DISCOVERY_USERVMSTATUS, str(discoveryStr), timestamp)
			ZabbixHelper.sendZabbix(metric)
		return

	@staticmethod
	def sendVMStatus(vm, isUp):
		if isUp == True:
			status = 1 # UP
		else:
			status = 2 # DOWN
		driver = HandlerConfigurator.get_vt_am_driver()
		vm_urn = driver.generate_sliver_urn(vm)
		timestamp = int(time.time())
		itemname = settings.ZBX_ITEM_USERVMSTATUS + '[' + str(vm_urn) + ']'
		metric = Metric(vm.name, str(itemname), status, timestamp)
		ZabbixHelper.sendZabbix(metric)
		return

	@staticmethod
	def sendZabbix(metric):
		ZabbixHelper.logger.debug("send Zabbix " + str(metric))
		result = send_to_zabbix([metric], settings.ZBX_SERVER_IP, settings.ZBX_SERVER_PORT)
		if(result == False):
			ZabbixHelper.logger.warn("cannot send VM status to Zabbix, continue anyway")
		return
