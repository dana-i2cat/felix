import os
import sys
import uuid, random 

#PYTHON_DIR = join(dirname(__file__), '/opt/ofelia/vt_manager/src/python/')
PYTHON_DIR = os.path.join(os.path.dirname(__file__), "../../..")

# This is needed because wsgi disallows using stdout
sys.stdout = sys.stderr

os.environ['DJANGO_SETTINGS_MODULE'] = 'vt_manager.settings'

sys.path.insert(0,PYTHON_DIR)


from vt_manager.models.VTServer import VTServer
from vt_manager.communication.utils.XmlHelper import *
from vt_manager.communication.XmlRpcClient import XmlRpcClient
from vt_manager.communication.southCommInterface import *
import xmlrpclib

url = 'https://expedient:expedient@192.168.254.170:8445/xmlrpc/plugin'
server = xmlrpclib.Server(url)
print server.ListResourcesAndNodes()

#AGENT DEVUELVE ONGOING
#import time
#time.sleep(10)
#response = XmlHelper.parseXmlString(xmlFileToString('failresponse.xml'))
#response.response.provisioning.action[0].id=actionUUID
#response.response.provisioning.action[0].status="ONGOING"
#sendAsync(XmlHelper.craftXmlClass(response))
#
#
##AGENT DEVUELVE FAIL
#time.sleep(10)
#response = XmlHelper.parseXmlString(xmlFileToString('failresponse.xml'))
#response.response.provisioning.action[0].id=actionUUID
#sendAsync(XmlHelper.craftXmlClass(response))
