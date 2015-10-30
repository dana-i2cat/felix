from vt_manager_kvm.models import *
from vt_manager_kvm.communication.utils.XmlUtils import *
import xmlrpclib

am = xmlrpclib.Server('https://expedient:expedient@192.168.254.193:8445/xmlrpc/agent')
xml = xmlFileToString('communication/utils/queryDelete.xml')

am.send(xml)




