from vt_manager.communication.utils.XmlHelper import XmlHelper
from vt_manager.models.Action import Action
from vt_manager.models.VirtualMachine import VirtualMachine
from vt_manager.controller.drivers.VTDriver import VTDriver
from vt_manager.communication.XmlRpcClient import XmlRpcClient
from vt_manager.controller.actions.ActionController import ActionController
from vt_manager.communication.sfa.vm_utils.SfaCommunicator import SfaCommunicator
from vt_manager.common.middleware.thread_local import thread_locals, pull
from vt_manager.models.reservation import Reservation
from vt_manager.models.VirtualMachineKeys import VirtualMachineKeys
from vt_manager.utils.contextualization.vm_contextualize import VMContextualize
import logging

class ProvisioningResponseDispatcher():

	'''
	Handles the Agent responses when action status changes
	'''

	@staticmethod
	def processResponse(rspec):
		logging.debug("PROCESSING RESPONSE processResponse() STARTED...")
		for action in rspec.response.provisioning.action:

			try:
				actionModel = ActionController.getAction(action.id)
			except Exception as e:
				logging.error("No action in DB with the incoming uuid\n%s", e)
				return

			'''
			If the response is for an action only in QUEUED or ONGOING status, SUCCESS or FAILED actions are finished
			'''
			#if str(actionModel.callBackUrl) == str(SfaCommunicator.SFAUrl): #Avoiding unicodes
			#	event = pull(str(action.id))
			#	event.send('continue')
			#	return

			if actionModel.getStatus() is Action.QUEUED_STATUS or Action.ONGOING_STATUS:
				logging.debug("The incoming response has id: %s and NEW status: %s",actionModel.uuid,actionModel.status)
                                was_creating = False
                                was_created = False
                           	actionModel.status = action.status
				actionModel.description = action.description
				actionModel.save()
				#Complete information required for the Plugin: action type and VM
				ActionController.completeActionRspec(action, actionModel)

				#XXX:Implement this method or some other doing this job
				vm = VTDriver.getVMbyUUID(actionModel.getObjectUUID())
                                if vm.state == "creating...":
                                    was_creating = True
                                elif vm.state == "starting...":
                                    was_created = True
				controller=VTDriver.getDriver(vm.Server.get().getVirtTech())
				failedOnCreate = 0
				if actionModel.getStatus() == Action.SUCCESS_STATUS:
					ProvisioningResponseDispatcher.__updateVMafterSUCCESS(actionModel, vm)

				elif actionModel.getStatus() == Action.ONGOING_STATUS:
					ProvisioningResponseDispatcher.__updateVMafterONGOING(actionModel, vm)

				elif actionModel.getStatus() == Action.FAILED_STATUS:
					failedOnCreate = ProvisioningResponseDispatcher.__updateVMafterFAILED(actionModel, vm)

				else:
					vm.setState(VirtualMachine.UNKNOWN_STATE)
				try:
                                        created = False
                                        vm_started = False
                                        if vm.state == "created (stopped)":
                                            created = True
                                        elif vm.state == "running":
                                            vm_started = True
                                        logging.debug("Sending response to plug-in in sendAsync")
                                        if str(vm.callBackURL) == 'SFA.OCF.VTM':
                                                print "\n\n\n\n========================\n\n\n\n"
                                                print "callback:", str(vm.callBackURL)
                                                # Start VM just after creating sliver/VM
                                                if created and was_creating:
                                                    from vt_manager.communication.sfa.drivers.VTSfaDriver import VTSfaDriver
                                                    driver = VTSfaDriver(None)
                                                    driver.crud_slice(vm.sliceName,vm.projectName, "start_slice")
                                                    return
     
                                                if was_created and vm_started:
                                                    ifaces = vm.getNetworkInterfaces()
                                                    for iface in ifaces:
                                                        if iface.isMgmt:
                                                            ip = iface.ip4s.all()[0].ip
                                                    
                                                    # Contextualize VMs
                                                    ProvisioningResponseDispatcher.__contextualize_vm(vm, ip)
                                                    print "right after contextualize vms..."
                                                    
                                                    print "\n\n\n\n========================\n\n\n\n"
                                                    # Cleaning up reservation objects
                                                    print "right before cleaning up vms..."
                                                    ProvisioningResponseDispatcher.__clean_up_reservations(vm.name)
                                                    print "right after cleaning up vms..."
                                                    print "\n\n\n\n========================\n\n\n\n"
					        return
                                                print "\n\n\n\n========================\n\n\n\n"
					XmlRpcClient.callRPCMethod(vm.getCallBackURL(), "sendAsync", XmlHelper.craftXmlClass(rspec))
					if failedOnCreate == 1:
						controller.deleteVM(vm)
						# Keep actions table up-to-date after each deletion
						actionModel.delete()
				except Exception as e:
					logging.error("Could not connect to Plugin in sendAsync\n%s",e)
					return
			
			#If response is for a finished action
			else:
				try:
					#XXX: What should be done if this happen?
					logging.error("Received response for an action in wrong state\n")
					XmlRpcClient.callRPCMethod(vm.getCallBackURL(), "sendAsync", XmlHelper.getProcessingResponse(Action.ACTION_STATUS_FAILED_TYPE, action, "Received response for an action in wrong state"))
				except Exception as e:
					logging.error(e)
					return

	@staticmethod
	def processresponseSync(rspec):
            logging.debug("PROCESSING RESPONSE processResponseSync() STARTED...")
            for action in rspec.response.provisioning.action:
                try:
                    actionModel = ActionController.getAction(action.id)
                except Exception as e:
                    logging.error("No action in DB with the incoming uuid\n%s", e)
                    return
                
                """
                If the response is for an action only in QUEUED or ONGOING status, SUCCESS or FAILED actions are finished
                """
                #if str(actionModel.callBackUrl) == str(SfaCommunicator.SFAUrl): #Avoiding unicodes
                #       event = pull(str(action.id))
                #       event.send('continue')
                #       return
                
                print "................................ actionModel.getStatus(): %s ................." % str(actionModel.getStatus())
                if actionModel.getStatus() is Action.QUEUED_STATUS or Action.ONGOING_STATUS:
                    logging.debug("The incoming response has id: %s and NEW status: %s",actionModel.uuid,actionModel.status)
                    actionModel.status = action.status
                    actionModel.description = action.description
                    actionModel.save()
                    #Complete information required for the Plugin: action type and VM
                    ActionController.completeActionRspec(action, actionModel)
                    
                    #XXX:Implement this method or some other doing this job
                    vm = VTDriver.getVMbyUUID(actionModel.getObjectUUID())
                    print "................... >> vm: ", vm.__dict__
                    controller = VTDriver.getDriver(vm.Server.get().getVirtTech())
                    failedOnCreate = 0
                    if actionModel.getStatus() == Action.SUCCESS_STATUS:
                        ProvisioningResponseDispatcher.__updateVMafterSUCCESS(actionModel, vm)
                    elif actionModel.getStatus() == Action.ONGOING_STATUS:
                        ProvisioningResponseDispatcher.__updateVMafterONGOING(actionModel, vm)
                    elif actionModel.getStatus() == Action.FAILED_STATUS:
                        failedOnCreate = ProvisioningResponseDispatcher.__updateVMafterFAILED(actionModel, vm)
                    else:
                        vm.setState(VirtualMachine.UNKNOWN_STATE)
                    
                    try:
                        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! aaaaaaaaaaaaaaaaaaaaaaaaa !!!!!!!!!!!!!!!!!"
                        logging.debug("Sending response to Plugin in sendAsync")
                        if str(actionModel.callBackUrl) == 'SFA.OCF.VTM':
                            print ">>>>>>> SFA.OCF.VTM\n\n\n"
                            if failedOnCreate:
                                print "........... failedOnCreate........."
                                expiring_slices = vm.objects.filter(sliceName=vm.sliceName,projectName=vm.projectName)
                                print "........... expiring_slices: %s ..........." % str(expiring_slices)
                                if len(expiring_slices)  == 1:
                                    expiring_slices[0].delete()
                        
                        # XXX No llega aqui, por tanto lo pongo en el anterior metodo
                        print "\n\n\n\n========================\n\n\n\n"
                        # Cleaning up reservation objects
                        print "right before cleaning up vms..."
                        ProvisioningResponseDispatcher.__clean_up_reservations(vm.name)
                        print "right after cleaning up vms..."
                        print "\n\n\n\n========================\n\n\n\n"
                       
                        XmlRpcClient.callRPCMethod(vm.getCallBackURL(), "sendSync", XmlHelper.craftXmlClass(rspec))
                        if failedOnCreate == 1:
                            controller.deleteVM(vm)
                            # Keep actions table up-to-date after each deletion
                            actionModel.delete()
                    except Exception as e:
                        logging.error("Could not connect to Plugin in sendSync\n%s",e)
                        return
            
                # If response is for a finished action
                else:
                    try:
                        #XXX: What should be done if this happen?
                        logging.error("Received response for an action in wrong state\n")
                        XmlRpcClient.callRPCMethod(vm.getCallBackURL(), "sendSync", XmlHelper.getProcessingResponse(Action.ACTION_STATUS_FAILED_TYPE, action, "Received response for an action in wrong state"))
                    except Exception as e:
                        logging.error(e)
                        return

	@staticmethod
	def __updateVMafterSUCCESS(actionModel, vm):
		if actionModel.getType() == Action.PROVISIONING_VM_CREATE_TYPE:
			vm.setState(VirtualMachine.CREATED_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_START_TYPE or actionModel.getType() == Action.PROVISIONING_VM_REBOOT_TYPE:
			vm.setState(VirtualMachine.RUNNING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_STOP_TYPE:
			vm.setState(VirtualMachine.STOPPED_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_DELETE_TYPE:
			controller = VTDriver.getDriver(vm.Server.get().getVirtTech())
			controller.deleteVM(vm)
			# Keep actions table up-to-date after each deletion
			actionModel.delete()
	
	@staticmethod
	def __updateVMafterONGOING(actionModel, vm):
		if actionModel.getType() == Action.PROVISIONING_VM_CREATE_TYPE:
			vm.setState(VirtualMachine.CREATING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_START_TYPE:
			vm.setState(VirtualMachine.STARTING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_STOP_TYPE:
			vm.setState(VirtualMachine.STOPPING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_DELETE_TYPE:
			vm.setState(VirtualMachine.DELETING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_REBOOT_TYPE:
			vm.setState(VirtualMachine.REBOOTING_STATE)

	@staticmethod
	def __updateVMafterFAILED(actionModel, vm):
		if  actionModel.getType() == Action.PROVISIONING_VM_START_TYPE:
			vm.setState(VirtualMachine.STOPPED_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_STOP_TYPE:
			vm.setState(VirtualMachine.RUNNING_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_REBOOT_TYPE:
			vm.setState(VirtualMachine.STOPPED_STATE)
		elif actionModel.getType() == Action.PROVISIONING_VM_CREATE_TYPE:
			failedOnCreate = 1	#VM is deleted after sending response to the plug-in because callBackUrl is required
			return failedOnCreate
		else:
			vm.setState(VirtualMachine.FAILED_STATE)
        
        @staticmethod
        def __clean_up_reservations(vm_name):
            try:
                print "vm_name...", vm_name
                print "reservation object:", Reservation.objects.get(name = vm_name)
                Reservation.objects.get(name = vm_name).delete()
            except Exception as e:
                print "Failed to delete reservation for VM with name: %s. Exception: %s" % (str(vm_name), e)
                return
        
        @staticmethod
        def __contextualize_vm(vm, ip):
            # SSH keys for users are passed to the VM right after it is started
            vm_keys = VirtualMachineKeys.objects.filter(slice_uuid=vm.sliceId, project_uuid=vm.projectId)
            print "vm_keys: ", vm_keys
            params = {
                "vm_address": str(ip) ,
                "vm_user": "root",
                "vm_password": "openflow",
            }
            print "context:", params
            vm_context = VMContextualize(**params)
            for vm_key in vm_keys:
                print "Adding %s's public key into VM. Key contents: %s" % (vm_key.get_user_name(), vm_key.get_ssh_key())
                vm_context.contextualize_add_pub_key(str(vm_key.get_user_name()), str(vm_key.get_ssh_key()))
