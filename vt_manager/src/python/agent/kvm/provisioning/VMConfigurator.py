# -*- coding: utf-8 -*-

from kvm.provisioning.configurators.ofelia.OfeliaDebianVMConfigurator import OfeliaDebianVMConfigurator
from kvm.provisioning.configurators.irati.IratiDebianVMConfigurator import IratiDebianVMConfigurator
from kvm.provisioning.configurators.spirent.SpirentCentOSVMConfigurator import SpirentCentOSVMConfigurator
from kvm.provisioning.configurators.mediacat.MediacatVMConfigurator import MediacatVMConfigurator
from kvm.provisioning.configurators.debian7.DebianWheezyVMConfigurator import DebianWheezyVMConfigurator
from utils.Logger import Logger

'''
	@author: AIST

	Configurator redirector	
'''


class VMConfigurator():
	logger = Logger.getLogger()
	
	@staticmethod
	def __getConfiguratorByNameAndOsType(configurator, os):
		if configurator and configurator != "":
			if configurator == MediacatVMConfigurator.getIdentifier():
				return MediacatVMConfigurator;
			elif configurator == IratiDebianVMConfigurator.getIdentifier():
				return IratiDebianVMConfigurator;
			elif configurator == SpirentCentOSVMConfigurator.getIdentifier():
				return SpirentCentOSVMConfigurator;
			elif configurator == DebianWheezyVMConfigurator.getIdentifier():
				return DebianWheezyVMConfigurator
		else:
			if os.lower() == "debian" or os.lower() == "ubuntu":
				return OfeliaDebianVMConfigurator
		
		raise Exception("Unknown configurator")	

	# #Public methods
	@staticmethod
	def configureVmDisk(vm, pathToMountPoint):
		VMConfigurator.__getConfiguratorByNameAndOsType(vm.xen_configuration.configurator,
														vm.operating_system_distribution).configureVmDisk(vm, pathToMountPoint)
					
	@staticmethod
	def createVmConfigurationFile(vm):
		VMConfigurator.__getConfiguratorByNameAndOsType(vm.xen_configuration.configurator,
														vm.operating_system_distribution).createVmConfigurationFile(vm)
