import os
import sys
from os.path import dirname, join, normpath

PYTHON_DIR = normpath(join(dirname(__file__), '../../../../src/'))
sys.path.insert(0,PYTHON_DIR)
PYTHON_DIR = normpath(join(dirname(__file__), '../../../../src/plugins/notification/'))
sys.path.insert(0,PYTHON_DIR)

from notificationcenter import NotificationCenter as nc

helloSignal = "hello"
otherSignal = "other"

def printMessage(message):
    print "\n\n###################################"
    print message
    print "###################################"

class Plugin():

    def __init__(self, name):
        self.name = name

    def handleSignal(self, sender, **kw):
        
        print "%s: Caught signal from %r, data %r" % (self.name, sender, kw)
        return 'received!'


    def handleHello(self, sender):
        print "%s: Caught Hello from %r" % (self.name, sender)
        return 'Hello received'

printMessage("Initialazing Plugins...")
p1 = Plugin("Plugin n1")    
p2 = Plugin("Plugin n2")
p3 = Plugin("Plugin n3")

printMessage("Getting signals from NC...")
hello = nc.getSignal(helloSignal)    
other = nc.getSignal(otherSignal)
print hello
print other

printMessage("Plugin n1 connected to other signal...")
other.connect(p1.handleSignal)

printMessage("Plugin n2 connected to hello signal...")
hello.connect(p2.handleHello)

printMessage("Plugin n3 connected to hello signal...")
hello.connect(p3.handleHello)

printMessage("Signal receivers...")
print hello.receivers
print other.receivers

printMessage("Plugin n1 sending hello...")
hello.send(p1)

printMessage("Plugin n2 sending other signal...")
other.send(p2, data="info")

printMessage("Disabling multicast in other signal...")
other.disableMulticast()

printMessage("Connecting Plugin 3 to other signal...")
try:
    other.connect(p3.handleSignal)
except:
    print "Could not connect to signal, it is unicast"

printMessage("Enabling multicast...")
other.enableMulticast()

printMessage("Connecting Plugin 3 to other signal...")
try:
    other.connect(p3.handleSignal)
except:
    print "Could not connect to signal, it is unicast"
