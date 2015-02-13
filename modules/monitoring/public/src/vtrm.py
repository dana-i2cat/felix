#!/usr/bin/python
'''
@author: bpuype

copyright 2014-2015 FP7 FELIX, iMinds

'''

from xmlrm import *

import xmlrpclib
import web
import threading, time
import xml.etree.ElementTree as ET

class VTRM:
        def _reset(self):
                parsed = urlparse(self.url.lower())
                assert parsed.scheme == "https"

                self.transport = None
                from M2Crypto.m2xmlrpclib import SSL_Transport
                from M2Crypto.SSL import Context
                self.transport = SSL_Transport(Context(protocol='tlsv1'))

                new_url = add_basic_auth(self.url, self.username, self.password)
                self.proxy = xmlrpclib.ServerProxy(str(new_url), transport=self.transport, verbose=False)

                #print self.proxy


        def __init__(self, **kwargs):
                self.url = kwargs.get('url',"")
                self.username = kwargs.get('username',"")
                self.password = kwargs.get('password',"")
                if self.url:
                        #print "asdfasdf"
                        self._reset()

        def listResources(self):
                return self.proxy.listResources("monitor", "", "")



class VTThread(threading.Thread):
        def __init__(self, vtrm, db):
                threading.Thread.__init__(self)
                self.vtrm = vtrm
                self.db = db
                self.interval = 120
                self.finished = threading.Event()

        def run(self):
                while not self.finished.is_set():
                        self.update_vtrm(self.vtrm, self.db)
                        self.finished.wait(self.interval)

        def update_vtrm(self, vtrm, db):
                print "Updating VT"
		
		for island in vtrm:
			# get xml data
			xml = vtrm[island].listResources()
			root = ET.fromstring(xml[1])
	
			# get db vtserver list
			island_vtservers = list(db.select('vtservers', where='island=$island', vars={'island':island}))

			# get list of server elements and their names
			serverdata = root.findall('./response/information/resources/server')
			xml_vtnames = [n.find('name').text for n in serverdata] 

			# check all db vtservers against xml data
			for server in island_vtservers:
				name = server['name']
				status = 0
				for s in serverdata:
					if s.find('name').text == name:
						status = 1
						xml_vtnames.remove(name)
				if server['status'] != status:
					db.update('vtservers', where="id = "+str(server['id']), status=status)

			# add anything from xml data that was not already in db
			
			#TBD



        def shutdown(self):
                self.finished.set()

