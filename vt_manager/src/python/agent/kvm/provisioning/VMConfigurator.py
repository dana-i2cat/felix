# -*- coding: utf-8 -*-

from kvm.provisioning.configurators.ofelia.OfeliaDebianVMConfigurator import OfeliaDebianVMConfigurator
from kvm.provisioning.configurators.irati.IratiDebianVMConfigurator import IratiDebianVMConfigurator
from kvm.provisioning.configurators.spirent.SpirentCentOSVMConfigurator import SpirentCentOSVMConfigurator
from kvm.provisioning.configurators.mediacat.MediacatVMConfigurator import MediacatVMConfigurator
from kvm.provisioning.configurators.debian7.DebianWheezyVMConfigurator import DebianWheezyVMConfigurator
from utils.Logger import Logger

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
