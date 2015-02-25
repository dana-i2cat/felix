import requests
import json
import yaml
import os

current_path = os.path.dirname(os.path.abspath( __file__ ))
conf_file_path = os.path.join(current_path, "../../../../conf/ryu-config.yaml")
stream = open(conf_file_path, "r")
config = yaml.load(stream)

host = str(config["host"])
port = str(config["rest_port"])
dpid = config["dpid"]

def addSwitchingRule(in_port, out_port, in_vlan, out_vlan):
    """
    params: in_port (int)
            out_port (int)
            in_vlan (int)
            out_vlan (int)
    """
    headers = {'content-type': 'application/json'}
    payload = {
                "dpid":dpid,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":0,
                "hard_timeout":0,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":in_vlan,
                             "in_port":in_port
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":out_vlan
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":out_port
                                }
                             ]
                }
    r = requests.post("http://" + host + ":" + port + "/stats/flowentry/add", data=json.dumps(payload), headers=headers)
    print r.status_code
    print r.headers
    print r.__dict__

def deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan):
    print "start"
    headers = {'content-type': 'application/json'}

    payload = {
                "dpid":dpid,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":0,
                "hard_timeout":0,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":in_vlan,
                             "in_port":in_port
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":out_vlan
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":out_port
                                }
                             ]
                }
    r = requests.post("http://" + host + ":" + port + "/stats/flowentry/delete", data=json.dumps(payload), headers=headers)
    print r.status_code
