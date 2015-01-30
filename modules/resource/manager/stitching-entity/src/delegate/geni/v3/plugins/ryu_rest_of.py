import requests

def addSwitchingRule():
    payload = {'key1': 'value1', 'key2': 'value2'}
    r = requests.post("http://httpbin.org/postg", data=payload)
    print r

addSwitchingRule()