import os
import sys
from os.path import dirname, join, normpath

PYTHON_DIR = normpath(join(dirname(__file__), '../../../../src/'))
sys.path.insert(0,PYTHON_DIR)
PYTHON_DIR = normpath(join(dirname(__file__), '../../../../src/plugins/policy/'))
sys.path.insert(0,PYTHON_DIR)

from policymanager import PolicyManager

scope1 = "myTable"
scope2 = "myTable2"

class Resquest():
    
    user = None 
    entity = None
    obj = None

class Thing():

    att1 = None
    att2 = None

mapping = {"att1":"metaObj['att1']",
           "att2":"metaObj['att2'"}
   
myThing = Thing()
myThing.att1=1024
myThing.att2=512


def printMessage(message):
    print "\n\n\n###################################"
    print message
    print "###################################" 

PolicyManager.initialize(scope1,mapping,"RegexParser","RAWFile",fileName="database/myPolicyEngine.db")
PolicyManager.initialize(scope2,mapping,"RegexParser","RAWFile",fileName="database/myPolicyEngine2.db")

printMessage("Adding rule...")

PolicyManager.addRule(scope1,"if ( att1 < 512 ) then accept do log denyMessage Memory is greater than 512 MB #Preventing VMs with more than 512 MB")
PolicyManager.dump(scope1)

PolicyManager.addRule(scope2,"if ( att1 < 128 ) then accept do log denyMessage Memory is greater than 512 MB #Preventing VMs with more than 512 MB")
PolicyManager.dump(scope2)

printMessage("Addunning Rule...")

PolicyManager.addRule(scope1,"if ( att2 < 512 ) then accept do log denyMessage Memory is greater than 512 MB #Preventing VMs with more than 512 MB")
PolicyManager.dump(scope1)


printMessage("Evaluating table " +scope1+"...")

try:
    PolicyManager.evaluate(scope1, myThing)
    printMessage("Policy passed!")
except Exception:
    printMessage("Policy NOT passed!")

printMessage("Evaluating table " +scope2+"...")

try:
    PolicyManager.evaluate(scope2, myThing)
    printMessage("Policy passed!")
except Exception:
    printMessage("Policy NOT passed!")

myThing.att1=128

printMessage("Evaluating again the table " +scope1+"...")

try:
    PolicyManager.evaluate(scope1, myThing)
    printMessage( "Policy passed!")
except Exception:
    printMessage( "Policy NOT passed!")

printMessage("Removing first rule...")

PolicyManager.removeRule(scope1, index=0)
PolicyManager.dump(scope1)

