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
	Irati Debian VM Configurator
'''
import shutil
import os
import jinja2 
import string
import subprocess
import re

from kvm.provisioning.HdManager import HdManager
from settings.settingsLoader import OXA_KVM_SERVER_KERNEL,OXA_KVM_SERVER_INITRD,OXA_DEBIAN_INTERFACES_FILE_LOCATION,OXA_DEBIAN_UDEV_FILE_LOCATION, OXA_DEBIAN_HOSTNAME_FILE_LOCATION, OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION
from utils.Logger import Logger


class IratiDebianVMConfigurator:
	
	logger = Logger.getLogger()

	''' Private methods '''
	@staticmethod
	def __configureInterfacesFile(vm,iFile):
		#Loopback
		iFile.write("auto lo\niface lo inet loopback\n\n")
		#Interfaces
		for inter in vm.xen_configuration.interfaces.interface  :
			if inter.ismgmt:
				#is a mgmt interface
				interfaceString = "auto "+inter.name+"\n"+\
				"iface "+inter.name+" inet static\n"+\
				"\taddress "+inter.ip +"\n"+\
				"\tnetmask "+inter.mask+"\n"

				if inter.gw != None and inter.gw != "":
					interfaceString +="\tgateway "+inter.gw+"\n"

				if inter.dns1 != None and inter.dns1 != "":
					interfaceString+="\tdns-nameservers "+inter.dns1

					if inter.dns2 != None and inter.dns2 != "":
						interfaceString+=" "+inter.dns2
				interfaceString +="\n\n"

				iFile.write(interfaceString)			 
			else:
				#is a data interface
				iFile.write("auto "+inter.name+"\n\n")


	@staticmethod
	def __configureUdevFile(vm,uFile):
		for inter in vm.xen_configuration.interfaces.interface:
			uFile.write('SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="'+inter.mac+'", ATTR{dev_id}=="0x0", ATTR{type}=="1", KERNEL=="eth*", NAME="'+inter.name+'"\n')

	@staticmethod
	def __configureHostname(vm,hFile):
		hFile.write(vm.name)		
	
	
	@staticmethod
	def __createFullvirtualizationFileHdConfigFile(vm,env):
		template_name = "fullVirtualizedFileHd.pt"
		template = env.get_template(template_name)	

		#Set vars&render		
		output = template.render(
		kernelImg=OXA_KVM_SERVER_KERNEL,
		initrdImg=OXA_KVM_SERVER_INITRD,
		hdFilePath=HdManager.getHdPath(vm),
		#swapFilePath=HdManager.getSwapPath(vm),
		vm=vm)	
			
		#write file
		cfile = open(HdManager.getConfigFilePath(vm),'w')
		cfile.write(output)
		cfile.close()

	''' Public methods '''

	@staticmethod
	def getIdentifier():
		return	IratiDebianVMConfigurator.__name__ 

	@staticmethod
	def _configureNetworking(vm,path):
		#Configure interfaces and udev settings	
		try:

			try:
				#Backup current files
				shutil.copy(path+OXA_DEBIAN_INTERFACES_FILE_LOCATION,path+OXA_DEBIAN_INTERFACES_FILE_LOCATION+".bak")	
				shutil.copy(path+OXA_DEBIAN_UDEV_FILE_LOCATION,path+OXA_DEBIAN_UDEV_FILE_LOCATION+".bak")
			except Exception as e:
				pass

			with open(path+OXA_DEBIAN_INTERFACES_FILE_LOCATION,'w') as openif:
				IratiDebianVMConfigurator.__configureInterfacesFile(vm,openif)
			with open(path+OXA_DEBIAN_UDEV_FILE_LOCATION,'w') as openudev:
				IratiDebianVMConfigurator.__configureUdevFile(vm,openudev)
		except Exception as e:
			IratiDebianVMConfigurator.logger.error(str(e))
			raise Exception("Could not configure interfaces or Udev file")

	@staticmethod
	def _configureLDAPSettings(vm,path):
		try:
			file1 = open(path+OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION, "r")
			text = file1.read() 
			file1.close() 
			file2 = open(path+OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION, "w")
			#Scape spaces and tabs
			projectName = string.replace(vm.project_name,' ','_')
			projectName = string.replace(projectName,'\t','__')
			file2.write(text.replace("__projectId","@proj_"+vm.project_id+"_"+projectName))
			file2.close() 
		except Exception as e:
			IratiDebianVMConfigurator.logger.error("Could not configure LDAP file!! - "+str(e))

	@staticmethod
	def _configureHostName(vm,path):
		try:
			with open(path+OXA_DEBIAN_HOSTNAME_FILE_LOCATION,'w') as openhost:
				IratiDebianVMConfigurator.__configureHostname(vm, openhost)
		except Exception as e:
			IratiDebianVMConfigurator.logger.error("Could not configure hostname;skipping.. - "+str(e))
	@staticmethod
	def _configureSSHServer(vm,path):
		try:
			IratiDebianVMConfigurator.logger.debug("Regenerating SSH keys...\n Deleting old keys...")
			subprocess.check_call("rm -f "+path+"/etc/ssh/ssh_host_*", shell=True, stdout=None)
			#subprocess.check_call("chroot "+path+" dpkg-reconfigure openssh-server ", shell=True, stdout=None)
			
			IratiDebianVMConfigurator.logger.debug("Creating SSH1 key; this may take some time...")
			subprocess.check_call("ssh-keygen -q -f "+path+"/etc/ssh/ssh_host_key -N '' -t rsa1", shell=True, stdout=None)
			IratiDebianVMConfigurator.logger.debug("Creating SSH2 RSA key; this may take some time...")
			subprocess.check_call("ssh-keygen -q -f "+path+"/etc/ssh/ssh_host_rsa_key -N '' -t rsa", shell=True, stdout=None)
			IratiDebianVMConfigurator.logger.debug("Creating SSH2 DSA key; this may take some time...")
			subprocess.check_call("ssh-keygen -q -f "+path+"/etc/ssh/ssh_host_dsa_key -N '' -t dsa", shell=True, stdout=None)
		except Exception as e:
			IratiDebianVMConfigurator.logger.error("Fatal error; could not regenerate SSH keys. Aborting to prevent VM to be unreachable..."+str(e))
			raise e


	#Public methods
	@staticmethod
	def createVmConfigurationFile(vm):

		#get env
		template_dirs = []
		template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates/'))
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dirs))

		if vm.xen_configuration.hd_setup_type == "full-file-image" and vm.xen_configuration.virtualization_setup_type == "hvm" :
			IratiDebianVMConfigurator.__createFullvirtualizationFileHdConfigFile(vm,env)
		else:
			raise Exception("type of file or type of virtualization not supported for the creation of kvm vm configuration file")	

	@staticmethod
	def configureVmDisk(vm, path):
		
		if not path or not re.match(r'[\s]*\/\w+\/\w+\/.*', path,re.IGNORECASE): #For security, should never happen anyway
			raise Exception("Incorrect vm path")

		#Configure networking
		IratiDebianVMConfigurator._configureNetworking(vm,path)
		IratiDebianVMConfigurator.logger.info("Network configured successfully...")
		
		#Configure LDAP settings 
		IratiDebianVMConfigurator._configureLDAPSettings(vm,path)
		IratiDebianVMConfigurator.logger.info("Authentication configured successfully...")
	
		#Configure Hostname
		IratiDebianVMConfigurator._configureHostName(vm,path)
		IratiDebianVMConfigurator.logger.info("Hostname configured successfully...")
		
		#Regenerate SSH keys
		IratiDebianVMConfigurator._configureSSHServer(vm,path)
		IratiDebianVMConfigurator.logger.info("SSH have been keys regenerated...")
