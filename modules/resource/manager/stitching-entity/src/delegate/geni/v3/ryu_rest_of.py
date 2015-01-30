import requests

def addSwitchingRule():
    print "start"
    payload = {
                "dpid":110533270894679,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":30,
                "hard_timeout":30,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":333,
                             "in_port":12
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":555
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":13
                                }
                             ]
                }
    r = requests.post("http://127.0.0.1:8080/stats/flowentry/add", data=payload)
    print r.status_code

def deleteSwitchingRule():
    print "start"
    payload = {
                "dpid":110533270894679,
                "cookie":1,
                "cookie_mask":1,
                "table_id":0,
                "idle_timeout":30,
                "hard_timeout":30,
                "priority":1,
                "flags":1,  
                 "match": {
                             "dl_vlan":333,
                             "in_port":12
                          }, 
                 "actions":[
                                 {
                                     "type":"SET_VLAN_VID",
                                     "vlan_vid":555
                                },
                                 {
                                     "type":"OUTPUT",
                                     "port":13
                                }
                             ]
                }
    r = requests.post("http://127.0.0.1:8080/stats/flowentry/delete", data=payload)
    print r.status_code

if __name__ == '__main__':
    # addSwitchingRule()
    deleteSwitchingRule()