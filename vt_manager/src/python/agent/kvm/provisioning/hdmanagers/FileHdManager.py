# -*- coding: utf-8 -*-
'''
	@author: AIST

	File-type Hd management routines
'''
import os
import shutil
import subprocess
import traceback
from utils.Logger import Logger
from settings.settingsLoader import OXA_FILEHD_CACHE_TEMPLATES,\
	OXA_FILEHD_REMOTE_TEMPLATES, OXA_FILEHD_CACHE_VMS, OXA_FILEHD_REMOTE_VMS,\
	OXA_FILEHD_NICE_PRIORITY, OXA_FILEHD_IONICE_CLASS,\
	OXA_FILEHD_IONICE_PRIORITY, OXA_FILEHD_USE_CACHE, OXA_KVM_DEBIAN_TEMPLATE_IMGFILE

OXA_FILEHD_HD_TMP_MP = "/tmp/oxa/hd"

class FileHdManager(object):
	'''
		File-type Hard Disk management routines
	'''
	
	logger = Logger.getLogger()

	# Enables/disables the usage of Cache directory
	__useCache = OXA_FILEHD_USE_CACHE

	# #Utils
	@staticmethod
	def subprocessCall(command, priority=OXA_FILEHD_NICE_PRIORITY, ioPriority=OXA_FILEHD_IONICE_PRIORITY,
						ioClass=OXA_FILEHD_IONICE_CLASS, stdout=None):
		try:
			wrappedCmd = "/usr/bin/nice -n " + str(priority) + " /usr/bin/ionice -c " + str(ioClass) + " -n " + str(ioPriority) + " " + command
			FileHdManager.logger.debug("Executing: " + wrappedCmd) 
			subprocess.check_call(wrappedCmd, shell=True, stdout=stdout)
		except Exception as e:
			FileHdManager.logger.error("Unable to execute command: " + command)
			raise e
		return

	# Debug string 
	@staticmethod
	def debugVM(vm):
		return " project:" + vm.project_id + ", slice:" + vm.slice_id + ", name:" + vm.name
	
	# Paths
	''' Returns the container directory for the VM in remote FS'''
	@staticmethod
	def getRemoteHdDirectory(vm):
		return  OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/"
	
	''' Returns the container directory for the VM in remote Cache, if used'''
	@staticmethod
	def getHdDirectory(vm):
		if FileHdManager.__useCache: 
			return  OXA_FILEHD_CACHE_VMS + vm.project_id + "/" + vm.slice_id + "/"
		else:
			return  OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/"
	
	''' Returns the path of the hd file in Cache, if used'''
	@staticmethod
	def getHdPath(vm):
		if FileHdManager.__useCache: 
			return OXA_FILEHD_CACHE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".img"
		else:
			return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".img"

	''' Returns the path of the hd file in Remote'''
	@staticmethod
	def getRemoteHdPath(vm):
		return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".img"
	
	''' Returns the path of the swap hd file in Cache, if used'''
	@staticmethod
	def getSwapPath(vm):
		if FileHdManager.__useCache: 
			return OXA_FILEHD_CACHE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + "_swap" + ".img"
		else:
			return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + "_swap" + ".img"
			
	''' Returns the path of the swap hd file in Remote'''
	@staticmethod
	def getRemoteSwapPath(vm):
		return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + "_swap" + ".img"
	
	''' Returns the path of the config file in Cache, if used'''
	@staticmethod
	def getConfigFilePath(vm):
		if FileHdManager.__useCache: 
			return OXA_FILEHD_CACHE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".conf"
		else:
			return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".conf"
	
	''' Returns the path of the config file in Remote'''
	@staticmethod
	def getRemoteConfigFilePath(vm):
		return OXA_FILEHD_REMOTE_VMS + vm.project_id + "/" + vm.slice_id + "/" + vm.name + ".conf"
			
	''' Returns the path of the temporally mounted Hd in the dom0 filesystem'''
	@staticmethod
	def getTmpMountedHdPath(vm):
		return OXA_FILEHD_HD_TMP_MP + vm.name + "_" + vm.uuid + "/"

	''' Returns the path of the templates origin''' 
	@staticmethod
	def getTemplatesPath(vm):
		if FileHdManager.__useCache: 
			return OXA_FILEHD_CACHE_TEMPLATES
		else:
			return OXA_FILEHD_REMOTE_TEMPLATES

	# #Hooks
	'''Pre-start Hook'''
	@staticmethod
	def startHook(vm):
		if not FileHdManager.isVMinCacheFS(vm):
			FileHdManager.moveVMToCacheFS(vm)
		return

	'''Pre-reboot Hook'''
	@staticmethod
	def rebootHook(vm):
		return

	'''Post-stop Hook'''
	@staticmethod
	def stopHook(vm):
		if FileHdManager.isVMinCacheFS(vm):
			FileHdManager.moveVMToRemoteFS(vm)
		return

	# #Hd management routines

	@staticmethod
	def __fileTemplateExistsOrImportFromRemote(filepath):
		# if Cache is not used skip
		if not FileHdManager.__useCache:
			return True	
	
		# Check cache
		if os.path.exists(OXA_FILEHD_CACHE_TEMPLATES + filepath):
			return True
		path = os.path.dirname(filepath)

		# Check remote	
		if os.path.exists(OXA_FILEHD_REMOTE_TEMPLATES + path):
			# import from remote to cache
			FileHdManager.logger.info("Importing image to cache directory:" + OXA_FILEHD_REMOTE_TEMPLATES + path + "->" + OXA_FILEHD_CACHE_TEMPLATES + path)
			try:
				# Copy all 
				FileHdManager.subprocessCall("/bin/cp " + str(OXA_FILEHD_REMOTE_TEMPLATES + path) + " " + str(OXA_FILEHD_CACHE_TEMPLATES + path))
			except Exception as e:
				FileHdManager.logger.error(str(e))
				FileHdManager.logger.error(traceback.format_exc())
				return False
			return True
		
		return False
	
	@staticmethod
	def clone(vm):
		try:
			# TODO: user authentication
			template_path = vm.xen_configuration.hd_origin_path
			if os.path.isfile(template_path) == False:
				FileHdManager.logger.warn("invalid hd_origin_path specified, use default. " + 
										"hd_origin_path = " + template_path)
				template_path = OXA_KVM_DEBIAN_TEMPLATE_IMGFILE
				
			vm_path = FileHdManager.getHdPath(vm)
			swap_path = FileHdManager.getSwapPath(vm)
			FileHdManager.logger.info("template_path = " + template_path)
			FileHdManager.logger.info("vm_path = " + vm_path)
			FileHdManager.logger.info("swap_path = " + swap_path)
			FileHdManager.logger.debug("Trying to clone " + vm_path
									+ " using " + template_path + " as backing file")

			if not os.path.exists(os.path.dirname(vm_path)):	
				os.makedirs(os.path.dirname(vm_path))
				
			# Create HD
			FileHdManager.logger.info("Creating disks...")
			FileHdManager.logger.info("qemu-img create -b " + template_path + " -f qcow2 " + vm_path)
			FileHdManager.subprocessCall("qemu-img create -b " + template_path + " -f qcow2 " + vm_path)
		except Exception as e:
			FileHdManager.logger.error("Could not clone image to working directory: " + str(e)) 
			raise Exception("Could not clone image to working directory" + FileHdManager.debugVM(vm))
		finally:
			FileHdManager.logger.info("finished") 
		return

	@staticmethod
	def delete(vm):
		try:
			if not FileHdManager.isVMinRemoteFS(vm):
				FileHdManager.moveVMToRemoteFS(vm)
		except Exception:
			pass
		try:
			os.remove(FileHdManager.getRemoteHdPath(vm))
		except Exception:
			pass
		try:
			os.remove(FileHdManager.getRemoteSwapPath(vm)) 
		except Exception:
			pass
		try:
			os.remove(FileHdManager.getRemoteConfigFilePath(vm))
		except Exception:
			pass
		return 
			
	# Mount/umount routines
	@staticmethod
	def mount(vm):
		path = FileHdManager.getTmpMountedHdPath(vm)
		FileHdManager.logger.info("path = " + path)
		if not os.path.isdir(path):
			os.makedirs(path)
	
		vm_path = FileHdManager.getHdPath(vm)
		FileHdManager.logger.info("guestmount -a " + str(vm_path) + " -m /dev/sda1 " + str(path))	
		FileHdManager.subprocessCall("guestmount -a " + str(vm_path) + " -m /dev/sda1 " + str(path))	
		return path

	@staticmethod
	def umount(path):
		FileHdManager.logger.info('guestunmount --retry=10 ' + str(path))
		FileHdManager.subprocessCall('guestunmount --retry=10 ' + str(path))
		# FileHdManager.subprocessCall('/bin/umount -d '+str(path))
		# remove dir
		os.removedirs(path)
		return	
		
	# Cache-Remote warehouse methods 
	@staticmethod
	def isVMinRemoteFS(vm):
		return os.path.exists(FileHdManager.getRemoteHdPath(vm)) 
	
	@staticmethod
	def isVMinCacheFS(vm):
		return os.path.exists(FileHdManager.getHdPath(vm))
		
	@staticmethod
	def moveVMToRemoteFS(vm):
		# if Cache is not used skip
		if not FileHdManager.__useCache:
			return	
	
		if FileHdManager.isVMinCacheFS(vm): 
			# create dirs if do not exist already
			try:
				os.makedirs(FileHdManager.getRemoteHdDirectory(vm))
			except Exception as e:
				FileHdManager.logger.error(str(e))
				FileHdManager.logger.error(traceback.format_exc())
				pass
			# Move all files
			shutil.move(FileHdManager.getHdPath(vm), FileHdManager.getRemoteHdPath(vm)) 
			shutil.move(FileHdManager.getSwapPath(vm), FileHdManager.getRemoteSwapPath(vm))
			shutil.move(FileHdManager.getConfigFilePath(vm), FileHdManager.getRemoteConfigFilePath(vm)) 
		else:
			raise Exception("Cannot find VM in CACHE FS" + FileHdManager.debugVM(vm))
		return	
	
	@staticmethod
	def moveVMToCacheFS(vm):
		# if Cache is not used skip
		if not FileHdManager.__useCache:
			return	
	
		if FileHdManager.isVMinRemoteFS(vm): 

			if FileHdManager.isVMinCacheFS(vm): 
				raise Exception("Machine is already in Cache FS" + FileHdManager.debugVM(vm))
				
			# create dirs if do not exist already
			try:
				os.makedirs(FileHdManager.getHdDirectory(vm))
			except Exception as e:
				FileHdManager.logger.error(str(e))
				FileHdManager.logger.error(traceback.format_exc())
				pass
	
			# Move all files
			shutil.move(FileHdManager.getRemoteHdPath(vm), FileHdManager.getHdPath(vm)) 
			shutil.move(FileHdManager.getRemoteSwapPath(vm), FileHdManager.getSwapPath(vm))
			shutil.move(FileHdManager.getRemoteConfigFilePath(vm), FileHdManager.getConfigFilePath(vm))
			
		else:
			raise Exception("Cannot find VM in REMOTE FS" + FileHdManager.debugVM(vm))
		return
	