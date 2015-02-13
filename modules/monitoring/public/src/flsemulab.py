#!/usr/bin/python
'''
@author: bpuype
'''

from xmlrm import *

import web
import json, urllib2
import threading, time

class FLSEMULAB:
        def __init__(self, **kwargs):
                self.url = kwargs.get('url',"")

        def count(self):
#		try:
		print "Getting "+self.url
		result = json.loads(urllib2.urlopen(self.url).read())
		count = int(result[0]["results"]["count"])
		return count
#		except:
			
#			return -1
		


class FLSThread(threading.Thread):
        def __init__(self, fls, db):
                threading.Thread.__init__(self)
                self.fls = fls
                self.db = db
                self.interval = 120
                self.finished = threading.Event()

        def run(self):
                while not self.finished.is_set():
                        self.update_emulab(self.fls, self.db)
                        self.finished.wait(self.interval)

        def update_emulab(self, fls, db):
                print "Updating FLSEMULAB"
		
		for island in fls:
			# get count data
			for name in fls[island].keys():
				emulab = fls[island][name]
				count = emulab.count()

				db.update('flsemulab', where='island=$island and name=$name', vars={'island':island, 'name':name}, count=count)


        def shutdown(self):
                self.finished.set()

