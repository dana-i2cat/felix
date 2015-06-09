# -*- coding: utf-8 -*-
'''
	@author: AIST

	Ofelia Debian VM Configurator
'''
import jinja2 
import os
import re
import shutil
import string
import subprocess

from kvm.provisioning.HdManager import HdManager
from settings.settingsLoader import *
from utils.Logger import Logger
from netaddr import *

class OfeliaDebianVMConfigurator:
	
	logger = Logger.getLogger()

	''' Private methods '''
	@staticmethod
	def __configureInterfacesFile(vm, iFile):
		# Loopback
		iFile.write("auto lo\n")
		iFile.write("iface lo inet loopback\n\n")
		# Interfaces
		for inter in vm.xen_configuration.interfaces.interface:
			if inter.ismgmt:
				# is a mgmt interface
				interfaceString = "auto " + inter.name + "\n" + \
				"iface " + inter.name + " inet static\n" + \
				"\taddress " + inter.ip + "\n" + \
				"\tnetmask " + inter.mask + "\n"

				if inter.gw != None and inter.gw != "":
					ipaddr = IPNetwork(str(inter.ip+ '/' + inter.mask))
					if ipaddr.is_private() == False:
						interfaceString += "\tgateway " + inter.gw + "\n"
					else:
						pass
					interfaceString += "\tup route add -net " + \
						str(ipaddr.network) + " netmask " + inter.mask + \
						" gw "+ inter.gw + " dev " + inter.name +"\n"

				if inter.dns1 != None and inter.dns1 != "":
					ipaddr = IPNetwork(str(inter.ip+ '/' + inter.mask))
					if ipaddr.is_private() == False:
						interfaceString += "\tdns-nameservers " + inter.dns1
					else:
						pass

				if inter.dns2 != None and inter.dns2 != "":
					ipaddr = IPNetwork(str(inter.ip+ '/' + inter.mask))
					if ipaddr.is_private() == False:
						interfaceString += " " + inter.dns2
					else:
						pass

				interfaceString += "\n\n"
				iFile.write(interfaceString)
			else:
				# is a data interface
				iFile.write("auto " + inter.name + "\n")
		return

	@staticmethod
	def __configureUdevFile(vm, uFile):
		for inter in vm.xen_configuration.interfaces.interface:
			uFile.write('SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="' + inter.mac
						+ '", ATTR{dev_id}=="0x0", ATTR{type}=="1", KERNEL=="eth*", NAME="'	 + inter.name + '"\n')

	@staticmethod
	def __configureHostname(vm, hFile):
		hFile.write(vm.name + "\n")

	@staticmethod
	def __configureHosts(vm, hostsFile):
		hostsFile.write("127.0.0.1 localhost\n")
		hostsFile.write("127.0.1.1 " + vm.name + "\n")
		hostsFile.write("\n")
		hostsFile.write("::1     localhost ip6-localhost ip6-loopback\n")
		hostsFile.write("ff02::1 ip6-allnodes\n")
		hostsFile.write("ff02::2 ip6-allrouters\n")
		return
	
	@staticmethod
	def __createConfigFile(vm, env):
		template_name = "kvm.template.xml"
		template = env.get_template(template_name)	

		# Set vars&render		
		output = template.render(vm_name=vm.name, vm_uuid=vm.uuid,
								vm_memory=vm.xen_configuration.memory_mb,
								vm_cpu=str(1),
								vm_imgfile=HdManager.getHdPath(vm),
								vm=vm)	
			
		# write file
		cfile = open(HdManager.getConfigFilePath(vm), 'w')
		cfile.write(output)
		cfile.close()


	''' Public methods '''

	@staticmethod
	def getIdentifier():
		return	OfeliaDebianVMConfigurator.__name__ 

	@staticmethod
	def _configureNetworking(vm, path):
		# Configure interfaces and udev settings	
		logger = OfeliaDebianVMConfigurator.logger
		try:

			try:
				# Backup current files
				logger.info("copy" + path + OXA_DEBIAN_INTERFACES_FILE_LOCATION
							+ " to " + path + OXA_DEBIAN_INTERFACES_FILE_LOCATION + ".bak")	
				shutil.copy(path + OXA_DEBIAN_INTERFACES_FILE_LOCATION,
							path + OXA_DEBIAN_INTERFACES_FILE_LOCATION + ".bak")	
				logger.info("copy " + path + OXA_DEBIAN_UDEV_FILE_LOCATION
                            + " to " + path + OXA_DEBIAN_UDEV_FILE_LOCATION + ".bak")
				shutil.copy(path + OXA_DEBIAN_UDEV_FILE_LOCATION,
							path + OXA_DEBIAN_UDEV_FILE_LOCATION + ".bak")
			except Exception as e:
				pass

			with open(path + OXA_DEBIAN_INTERFACES_FILE_LOCATION, 'w') as openif:
				logger.info("write " + path + OXA_DEBIAN_INTERFACES_FILE_LOCATION)
				OfeliaDebianVMConfigurator.__configureInterfacesFile(vm, openif)
			with open(path + OXA_DEBIAN_UDEV_FILE_LOCATION, 'w') as openudev:
				logger.info("write " + path + OXA_DEBIAN_UDEV_FILE_LOCATION)
				OfeliaDebianVMConfigurator.__configureUdevFile(vm, openudev)
		except Exception as e:
			OfeliaDebianVMConfigurator.logger.error(str(e))
			raise Exception("Could not configure interfaces or Udev file")

	@staticmethod
	def _configureLDAPSettings(vm, path):
		try:
			file1 = open(path + OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION, "r")
			text = file1.read() 
			file1.close() 
			file1 = open(path + OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION, "w")
			# Scape spaces and tabs
			projectName = string.replace(vm.project_name, ' ', '_')
			projectName = string.replace(projectName, '\t', '__')
			file1.write(text.replace("__projectId", "@proj_" + vm.project_id + "_" + projectName))
			file1.close() 
		except Exception as e:
			OfeliaDebianVMConfigurator.logger.error("Could not configure LDAP file!! - " + str(e))

	@staticmethod
	def _configureHostName(vm, path):
		logger = OfeliaDebianVMConfigurator.logger
		try:
			with open(path + OXA_DEBIAN_HOSTNAME_FILE_LOCATION, 'w') as openhost:
				logger.info("write " + path + OXA_DEBIAN_HOSTNAME_FILE_LOCATION)
				OfeliaDebianVMConfigurator.__configureHostname(vm, openhost)
			with open(path + OXA_DEBIAN_HOSTS_FILE_LOCATION, 'w') as openhosts:
				logger.info("write " + path + OXA_DEBIAN_HOSTS_FILE_LOCATION)
				OfeliaDebianVMConfigurator.__configureHosts(vm, openhosts)
		except Exception as e:
			OfeliaDebianVMConfigurator.logger.error("Could not configure hostname;skipping.. - " + str(e))

	@staticmethod
	def _configureSSHServer(vm, path):
		logger = OfeliaDebianVMConfigurator.logger
		try:
			logger.debug("Regenerating SSH keys...\n Deleting old keys...")
			logger.debug("rm -f " + path + "/etc/ssh/ssh_host_*")
			subprocess.check_call("rm -f " + path + "/etc/ssh/ssh_host_*", shell=True, stdout=None)
			
			logger.debug("Creating SSH1 key; this may take some time...")
			logger.debug("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_key -N '' -t rsa1")
			subprocess.check_call("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_key -N '' -t rsa1",
								 shell=True, stdout=None)
			logger.debug("Creating SSH2 RSA key; this may take some time...")
			logger.debug("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_rsa_key -N '' -t rsa")
			subprocess.check_call("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_rsa_key -N '' -t rsa",
								 shell=True, stdout=None)
			logger.debug("Creating SSH2 DSA key; this may take some time...")
			logger.debug("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_dsa_key -N '' -t dsa")
			subprocess.check_call("ssh-keygen -q -f " + path + "/etc/ssh/ssh_host_dsa_key -N '' -t dsa",
								 shell=True, stdout=None)
		except Exception as e:
			OfeliaDebianVMConfigurator.logger.error("Fatal error; could not regenerate SSH keys. Aborting to prevent VM to be unreachable..." + str(e))
			raise e


	# Public methods
	@staticmethod
	def createVmConfigurationFile(vm):
		# get env
		template_dirs = []
		template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates/'))
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dirs))

		if vm.xen_configuration.hd_setup_type == "file-image":
			OfeliaDebianVMConfigurator.__createConfigFile(vm, env)
		else:
			raise Exception("type of file or type of virtualization not supported for the creation of kvm vm configuration file")	

	@staticmethod
	def configureVmDisk(vm, path):
		if not path or not re.match(r'[\s]*\/\w+\/\w+\/.*', path, re.IGNORECASE):  # For security, should never happen anyway
			raise Exception("Incorrect vm path")

		# Configure networking
		OfeliaDebianVMConfigurator._configureNetworking(vm, path)
		OfeliaDebianVMConfigurator.logger.info("Network configured successfully...")
		
		# Configure LDAP settings 
		# OfeliaDebianVMConfigurator._configureLDAPSettings(vm, path)
		# OfeliaDebianVMConfigurator.logger.info("Authentication configured successfully...")
	
		# Configure /etc/hostname and /etc/hosts
		OfeliaDebianVMConfigurator._configureHostName(vm, path)
		OfeliaDebianVMConfigurator.logger.info("Hostname configured successfully...")
		
		# Regenerate SSH keys
		OfeliaDebianVMConfigurator._configureSSHServer(vm, path)
		OfeliaDebianVMConfigurator.logger.info("SSH have been keys regenerated...")
