import requests
import json

def addSwitchingRule():
    print "start"
    headers = {'content-type': 'application/json'}
    payload = {
                "dpid":0000000000000001,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":30,
                "hard_timeout":30,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":333,
                             "in_port":1
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":555
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":2
                                }
                             ]
                }
    r = requests.post("http://127.0.0.1:8080/stats/flowentry/add", data=json.dumps(payload), headers=headers)
    print r.status_code
    print r.headers
    print r.__dict__

def deleteSwitchingRule():
    print "start"
    headers = {'content-type': 'application/json'}

    payload = {
                "dpid":0000000000000001,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":30,
                "hard_timeout":30,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":333,
                             "in_port":1
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":555
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":2
                                }
                             ]
                }
    r = requests.post("http://127.0.0.1:8080/stats/flowentry/delete", data=json.dumps(payload), headers=headers)
    print r.status_code

if __name__ == '__main__':
    # addSwitchingRule()
    deleteSwitchingRule()