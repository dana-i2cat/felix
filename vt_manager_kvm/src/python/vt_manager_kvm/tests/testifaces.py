from vt_manager_kvm.communication.utils.XmlUtils import *
from vt_manager_kvm.controller.Translator import Translator
from vt_manager_kvm.models import *
from vt_manager_kvm.controller.ProvisioningDispatcher import *
#from vt_manager_kvm.communication import *

s = xmlFileToString('../agent/utils/xml/query.xml')
r = XmlHelper.parseXmlString(s)
VMmodel = Translator.VMtoModel(r.query.provisioning.action[0].virtual_machine)
ProvisioningDispatcher.setVMinterfaces(VMmodel, r.query.provisioning.action[0].virtual_machine)
print VMmodel.getMacs()
print VMmodel.getMacs()[0].getMac()
