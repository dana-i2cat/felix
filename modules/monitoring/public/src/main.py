#!/usr/bin/python
'''
@author: bpuype
'''

from settings import *
from vtrm import *
from flsemulab import *

import xmlrpclib
import web
from urlparse import urlparse
import threading, time



def add_basic_auth(uri, username=None, password=None):
    parsed = urlparse(uri.lower())
    if username:
        if password:
            new_url = "%s://%s:%s@%s%s" % (parsed.scheme,
                                           username,
                                           password,
                                           parsed.netloc,
                                           parsed.path)
        else:
            new_url = "%s://%s@%s%s" % (parsed.scheme,
                                        username,
                                        parsed.netloc,
                                        parsed.path)
    else:
        new_url = uri
    return new_url



class OFRM:
	def _reset(self):
		parsed = urlparse(self.url.lower())
		assert parsed.scheme == "https"

		self.transport = None
		from M2Crypto.m2xmlrpclib import SSL_Transport
		from M2Crypto.SSL import Context
		self.transport = SSL_Transport(Context(protocol='tlsv1'))

		new_url = add_basic_auth(self.url, self.username, self.password)
		self.proxy = xmlrpclib.ServerProxy(str(new_url), transport=self.transport, verbose=True)

		print self.proxy

				



	def __init__(self, **kwargs):
		self.url = kwargs.get('url',"")
		self.username = kwargs.get('username',"")
		self.password = kwargs.get('password',"")
		if self.url:
			print "asdfasdf"
			self._reset()

	def get_switches():
		return self.proxy.get_switches()

def describe_island(island):
	try:
		file = open("static/"+island+".txt")
		return file.read()
	except:
		return "" 
	
def describe_switches(island):
	
	output = '<table class="switches"><tr><th colspan="4">Inventory of OpenFlow switches in the testbed</th></tr>\n'
	output += '<tr><th>Manufacturer</th><th>Name</th><th>Model</th><th>Datapath ID</th><th>Status</th></tr>\n'
	alt = False
	for switch in list(db.select('switches', where='island=$island', vars={'island': island})):
		if alt:
			output += '<tr class="alt">\n'
		else:
			output += '<tr>\n'
		output += '<td>' + switch['manufacturer'] + '</td>\n'
		output += '<td>' + switch['name'] + '</td>\n'
		output += '<td>' + switch['model'] + '</td>\n'
		output += '<td>' + switch['dpid'] + '</td>\n'
		status = switch['status']
		if status:
			css_class="resourceup"
			html_status="up"
		else:
			css_class="resourcedown"
			html_status="down"
		output += '<td class="'+css_class+'">' + html_status + '</td>\n'
		output += '</tr>\n'
		alt = not alt
	output += '</table>'
	return output

def describe_servers(island):

	output = '<table class="switches"><tr><th colspan="5">Inventory of servers in the testbed</th></tr>\n'
	output += '<tr><th>Model</th><th>Name</th><th>OS</th><th>RAM</th><th>Type</th><th>Status</th></tr>\n'
	alt = False

	vtservers = list(db.select('vtservers', where='island=$island', vars={'island': island}))
	if len(vtservers) == 0:
		return "" 

	for server in vtservers:		
		if alt:
			output += '<tr class="alt">\n'
		else:
			output += '<tr>\n'
		output += '<td>' + server['model'] + '</td>\n'
		output += '<td>' + server['name'] + '</td>\n'
		output += '<td>' + server['OS'] + '</td>\n'
		output += '<td>' + server['RAM'] + '</td>\n'
		output += '<td>' + server['type'] + '</td>\n'
		status = server['status']
		if status:
			css_class="resourceup"
			html_status="VT ok"
		else:
			css_class="resourcedown"
			html_status="down"
		output += '<td class="'+css_class+'">' + html_status + '</td>\n'
	
		output += '</tr>\n'
		alt = not alt
	output += '</table>'
	return output

def describe_emulabs(island):
	output = '<table class="emulabs"><tr><th colspan="2">Inventory of Emulab deployments testbed</th></tr>\n'
	output += '<tr><th>Name</th><th>Machines</th><th>Status</th></tr>\n'

	alt = False

	emulabs = list(db.select('flsemulab', where='island=$island', vars={'island': island}))
	if len(emulabs) == 0:
		return ""

	for emulab in emulabs:
		if alt:
			output += '<tr class="alt">\n'
		else:
			output += '<tr>\n'
		output += '<td>' + emulab['name'] + '</td>\n'
		output += '<td>' + emulab['machines'] + '</td>\n'
		count = emulab['count']
		if count >= 0:
			css_class="resourceup"
			html_status=str(count)+' available'
		else:
			css_class="resourcedown"
			html_status="down"
		output += '<td class="'+css_class+'">' + html_status + '</td>\n'
		output += '</tr>\n'
		alt = not alt
		
	output += '</table>'
	return output


def describe_links(island):
	
	output = '<table class="links"><tr><th colspan="7">Switch connectivity</th></tr>\n'
	output += '<tr><th>Switch</th><th>DPID</th><th>Port</th><th class="linkarrow"></th><th>Port</th><th>DPID</th><th>Switch</th><th>Status</th></tr>\n'
	alt = False

	switches = list(db.select('switches'))

	for link in list(db.select('links', where='island=$island', vars={'island': island})):
		srcname = dstname = 'unknown'
		sr = [s for s in switches if s['dpid'] == link['sdpid']]
		if len(sr)>0:
			srcname = sr[0]['name']
		dr = [s for s in switches if s['dpid'] == link['ddpid']]
		if len(dr)>0:
			dstname = dr[0]['name']

		if alt:
			output += '<tr class="alt">\n'
		else:
			output += '<tr>\n'
		output += '<td>' + srcname + '</td>\n'
		output += '<td>' + link['sdpid'] + '</td>\n'
		output += '<td>' + str(link['sport']) + '</td>\n'
		output += '<td class="linkarrow">&lt;&mdash;&gt;</td>\n'
		output += '<td>' + str(link['dport']) + '</td>\n'
		output += '<td>' + link['ddpid'] + '</td>\n'
		output += '<td>' + dstname + '</td>\n'
		status = link['status']
		if status:
			css_class="resourceup"
			html_status="up"
		else:
			css_class="resourcedown"
			html_status="down"
		output += '<td class="'+css_class+'">' + html_status + '</td>\n'
		output += '</tr>\n'
		alt = not alt
	output += '</table>'
	return output

def updatetime(island):
	i = db.select('islands', where='name=$island', vars={'island': island} )

 	return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(i[0]['updatetime']) )


db = web.database(dbn='sqlite', db='monitor.db')

urls = (
	'/island/(.*)', 'get_island'
)
moniapp = web.application(urls, globals())
render = web.template.render('templates')

class get_island:
	def GET(self, island):
		global switches
		if island in ISLANDS.keys(): 
			return render.island(island=island, islanddescription=describe_island(island), sdndescription=describe_switches(island), crdescription=describe_servers(island), linkstatus=describe_links(island), emulabdescription=describe_emulabs(island), time=updatetime(island) )
		else:
			return web.notfound()


class OFThread(threading.Thread):
	def __init__(self, ofrm, db):
		threading.Thread.__init__(self)
		self.ofrm = ofrm
		self.db = db
		self.interval = 120
		self.finished = threading.Event()

	def run(self):
		while not self.finished.is_set():
			self.update_ofrm(self.ofrm, self.db)
			self.finished.wait(self.interval)

	def update_ofrm(self, ofrm, db):
		print "Updating OpenFlow"
		# make recurring event (1 min.)
		for island in ofrm:
			try:
				switchdata = ofrm[island].proxy.get_switches()
			
				linkdata = ofrm[island].proxy.get_links()
			except:
				continue
	
			island_switches = list(db.select('switches', where='island=$island', vars={'island':island}))
			
			for switch in island_switches:
				dpid = switch['dpid']
				status = 0			
				l = [x for x in switchdata if x[0] == dpid]
				if len(l) > 0:
					status = 1	
				if switch['status'] != status:
					db.update('switches', where="id = "+str(switch['id']), status=status)
	
			#print sdndata[island]
			
			island_links = list(db.select('links', where='island=$island', vars={'island':island}))
	
			#links from monitoring
			for link in linkdata:
				link.append(False)

			#check know links in db for status updates in links from monitoring
			for link in island_links:
				sdpid = link['sdpid']
				ddpid = link['ddpid']
				sport = str(link['sport'])
				dport = str(link['dport'])
				status = 0
				for i, l in enumerate(linkdata):
					if (l[0] == sdpid and l[1] == sport and  l[2] == ddpid and l[3] == dport) \
					  or (l[0] == ddpid and l[1] == dport and l[2] == sdpid and l[3] == sport):
						status = 1
						linkdata[i][-1] = True
				if link['status'] != status:
					db.update('links', where="id = "+str(link['id']), status=status)

			print linkdata

			#update links from monitoring not in db
			for link in [x for x in linkdata if x[-1] == False]:
	                        srcdpid = link[0]
	                        srcport = link[1]
	                        dstdpid = link[2]
	                        dstport = link[3]
        	                if srcdpid > dstdpid:
	                                dstdpid,srcdpid = srcdpid,dstdpid
	                                dstport,srcport = srcport,dstport

                                db.insert('links', island=island, sdpid=srcdpid, sport=srcport, ddpid=dstdpid, dport=dstport, status=1)

				
				

			db.update('islands', where='name=$island', updatetime=int(time.time()), vars={'island': island} )

	def shutdown(self):
		self.finished.set()


def main():
	try:
		db.query('''DROP TABLE islands''')
		db.query('''DROP TABLE switches''' )
		db.query('''DROP TABLE links''' )
		db.query('''DROP TABLE vtservers''' )
		db.query('''DROP TABLE flsemulab''' )
	except: 
		pass
	
	#create temporary table for update times
	db.query('''CREATE TABLE islands (
	  id INTEGER NOT NULL PRIMARY KEY,
	  name VARCHAR(32) NOT NULL,
	  updatetime INTEGER NOT NULL)''')

	#create temporary table for switches
	db.query('''CREATE TABLE switches ( 
	  id INTEGER NOT NULL PRIMARY KEY,
	  island VARCHAR(32) NOT NULL,
	  manufacturer VARCHAR(32) NOT NULL,
          name VARCHAR(32) NOT NULL,
          model VARCHAR(64) NOT NULL,
          dpid VARCHAR(24) NOT NULL,
	  status INTEGER)''')

	#create temporary table for links
	db.query('''CREATE TABLE links (
	  id INTEGER NOT NULL PRIMARY KEY,
	  island VARCHAR(32) NOT NULL,
	  sdpid VARCHAR(24) NOT NULL,
	  sport INTEGER,
	  ddpid VARCHAR(24) NOT NULL,
	  dport INTEGER,
	  status INTEGER NOT NULL)''')

	#create temporary table for vtservers
	db.query('''CREATE TABLE vtservers (
	  id INTEGER NOT NULL PRIMARY KEY,
	  island VARCHAR(32) NOT NULL,
          model VARCHAR(32) NOT NULL,
	  name VARCHAR(32) NOT NULL,
	  OS VARCHAR(64) NOT NULL,
          RAM VARCHAR(16),
	  type VARCHAR(16) NOT NULL,
	  status INTEGER)''')

	#create temporary table for flsemulab
	db.query('''CREATE TABLE flsemulab (
	  id INTEGER NOT NULL PRIMARY KEY,
	  island VARCHAR(32) NOT NULL,
	  name VARCHAR(32) NOT NULL,
	  machines VARCHAR(32) NOT NULL,
	  count INTEGER)''')
	
	#create temporary table for interfaces (switch-server)
	#db.query('''CREATE TABLE interfaces (
	#  id INTEGER NOT NULL PRIMARY KEY,
	#  island VARCHAR(32) NO NULL,
	#  dpid VARCHAR(24) NOT NULL,
	#  port INTEGER,
        #  name VARCHAR(32) NOT NULL,
        #  intf VARCHAR(16) NOT NULL
        #)''')

	ofrm={}
	vtrm={}
	fls={}
	for key in ISLANDS:
		db.insert('islands', name=key, updatetime=int(time.time()) )

		# fls monitor
		if 'flsemulab' in ISLANDS[key].keys():
			flsemulab = ISLANDS[key]['flsemulab']

			fls[key] = {}
			for emulab in flsemulab:
				name = emulab['name']
				machines = emulab['machines']

				# create url fetchers
				fls[key][name] = FLSEMULAB(url = emulab['url'])

				# create db entries
				db.insert('flsemulab', island=key, name=name, machines=machines, count=-1)

		# vt resources
		if 'vt' in ISLANDS[key].keys():
			vt = ISLANDS[key]['vt']
	
			vtrm[key] = VTRM(url=vt['url'], username=vt['username'], password=vt['password'])

			for server in ISLANDS[key]['vt']['servers']:
				model = server['model']
				name = server['name']
				OS = server['OS']
				RAM = server['RAM']
				type = server['type']
				
				db.insert('vtservers', island=key, model=model, name=name, OS=OS, RAM=RAM, type=type, status=0)
			

		# sdn resources			
		sdn = ISLANDS[key]['sdn']
		print sdn
		ofrm[key] = OFRM(url=sdn['url'],
		                 username=sdn['username'], 
		                 password=sdn['password'])
#	ofrm = OFRM(url="https://10.216.4.7:8443/xmlrpc/xmlrpc/", username="clearinghouse", password="optin-iminds-24512")
		for switch in ISLANDS[key]['sdn']['switches']:
			db.insert('switches', island=key, manufacturer=switch['manu'], name=switch['name'], 
			          model=switch['model'], dpid=switch['dpid'], status=0)
		#links[key] = ISLANDS[key]['sdn']['links']
	
		for link in ISLANDS[key]['sdn']['links']:
			#check for existing link detected in opposite direction	
			srcdpid = link[0]
			srcport = link[1]
			dstdpid = link[2]
			dstport = link[3]
			if srcdpid > dstdpid:
				dstdpid,srcdpid = srcdpid,dstdpid
				dstport,srcport = srcport,dstport
			
			l = list(db.select('links', where='island=$key and sdpid=$srcdpid and sport=$srcport and ddpid=$dstdpid and dport=$dstport',
			               vars=locals()))
			if len(l) == 0:
				db.insert('links', island=key, sdpid=srcdpid, sport=srcport, ddpid=dstdpid, dport=dstport, status=0)
		

	ofthread = OFThread(ofrm, db)
	ofthread.start()

	vtthread = VTThread(vtrm, db)
	vtthread.start()

	flsthread = FLSThread(fls, db)
	flsthread.start()
	
	#moniapp.run()
	web.httpserver.runsimple(moniapp.wsgifunc(), ("0.0.0.0", PORT))

	ofthread.shutdown()
	vtthread.shutdown()
	flsthread.shutdown()

if __name__ == "__main__":
	main()
