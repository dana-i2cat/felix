# -*- coding: utf-8 -*-

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
	Mediacat VM Configurator
'''
import os
import jinja2 
import subprocess

from kvm.provisioning.hdmanagers.LVMHdManager import LVMHdManager
from kvm.provisioning.HdManager import HdManager
from settings.settingsLoader import OXA_KVM_SERVER_KERNEL,OXA_KVM_SERVER_INITRD

class MediacatVMConfigurator:

	''' Private methods '''
	@staticmethod
	def __createParavirtualizationVM(vm):
		swap = 0
		if len(vm.xen_configuration.users.user) == 1 and vm.xen_configuration.users.user[0].name == "root":
			passwd = str(vm.xen_configuration.users.user[0].password)
		
		if vm.xen_configuration.memory_mb < 1024:
			swap = vm.xen_configuration.memory_mb*2
		else:
			swap = 1024
		
		p = subprocess.Popen(['/usr/bin/kvm-create-image','--hostname=' + vm.name,
							'--size=' + str(vm.xen_configuration.hd_size_gb) + 'Gb','--swap=' + str(swap) + 'Mb',
							'--memory=' + str(vm.xen_configuration.memory_mb) + 'Mb','--arch=amd64',
							'--password=' + passwd,'--output=' + LVMHdManager.getConfigFileDir(vm),
							'--role=udev'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		p.wait()

	@staticmethod
	def __createHVMFileHdConfigFile(vm,env):
		template_name = "mediacatHVMFileHd.pt"
		template = env.get_template(template_name)
		#Set vars&render
		output = template.render(
								kernelImg=OXA_KVM_SERVER_KERNEL,
								initrdImg=OXA_KVM_SERVER_INITRD,
								vm=vm)

		#write file
		cfile = open(HdManager.getConfigFilePath(vm),'w')
		cfile.write(output)
		cfile.close()
	

	#Public methods	
	@staticmethod
	def getIdentifier():
		return	MediacatVMConfigurator.__name__ 

	@staticmethod
	def configureVmDisk(vm,path):
		return

	@staticmethod
	def createVmConfigurationFile(vm):
		#get env
		template_dirs = []
		template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates/'))
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dirs))

		if vm.xen_configuration.hd_setup_type == "logical-volume-image" and vm.xen_configuration.virtualization_setup_type == "paravirtualization":
			MediacatVMConfigurator.__createParavirtualizationVM(vm)
		elif vm.xen_configuration.hd_setup_type == "logical-volume-image" and vm.xen_configuration.virtualization_setup_type == "hardware-assisted-virtualization":
			MediacatVMConfigurator.__createHVMFileHdConfigFile(vm,env) 
		else:
			raise Exception("type of file or type of virtualization not supported for the creation of kvm vm configuration file")	
	
