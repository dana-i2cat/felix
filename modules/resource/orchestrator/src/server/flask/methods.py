from flask import current_app
from flask import Response
from functools import wraps
from lxml import etree

import re


CLI_UNAVAILABLE_MSG = "Method only available via REST API"
GUI_UNAVAILABLE_MSG = "Method only available via GUI"

def parse_output_json(output):
    resp = Response(str(output), status=200, mimetype="application/json")
    return resp

def error_on_unallowed_method(output):
    resp = Response(str(output), status=405, mimetype="text/plain")
    return resp

def get_user_agent():
    from flask import request
    user_agent = "curl"
    try:
        user_agent = request.environ["HTTP_USER_AGENT"]
    except:
        pass
    return user_agent

def warn_must_use_gui():
    user_agent = get_user_agent()
    if "curl" in user_agent:
        return error_on_unallowed_method("Method not supported. Details: %s" % GUI_UNAVAILABLE_MSG)

def warn_must_use_cli():
    user_agent = get_user_agent()
    if "curl" not in user_agent:
        return error_on_unallowed_method("Method not supported. Details: %s" % CLI_UNAVAILABLE_MSG)

def check_cli_user_agent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        check_ua = warn_must_use_cli()
        if check_ua is not None:
            return check_ua
        else:
            return func(*args, **kwargs)
    return wrapper

def check_gui_user_agent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        check_ua = warn_must_use_gui()
        if check_ua is not None:
            return check_ua
        else:
            return func(*args, **kwargs)
    return wrapper

def get_peers():
    #domain_routing = g.mongo.db[current_app.db].domain.routing.find()
    domain_routing = [ p for p in current_app.mongo.get_configured_peers() ]
    # Retrieve domain URN per peer
    for route in domain_routing:
        try:
            peer_urns = []
            assoc_peers = current_app.mongo.get_info_peers({"_ref_peer": route["_id"]})
            for r in range(0, assoc_peers.count()):
                peer_urns.append(assoc_peers.next().get("domain_urn"))
            route["urn"] = peer_urns
            del route["_id"]
        except:
            pass
    return domain_routing

def get_used_tn_vlans():
    #tn_vlans = {"i2cat": [1500], "aist": [1200], "aist2": ["1490"]}
    tn_vlans = dict()
    slice_monitoring = [ p for p in current_app.mongo.get_slice_monitoring_info() ]
    for slice_mon in slice_monitoring:
        if slice_mon is not None:        
            slice_mon_tree = etree.fromstring(slice_mon)
            #slice_mon_tree.xpath("link//link_type[contains(@name, '%s')]" % ("virtual_link"))
            #slice_mon_tree.xpath("link_type[@name='%s']" % ("tn"))
            #slice_mon_tree.xpath("topology_list//topology//link_type[@name='%s']" % ("tn"))
            tn_link = slice_mon_tree.xpath("topology//link[@type='tn'][contains(@id, 'urn')]")
            if tn_link is None:
                break

            link_id = tn_link[0].get("id")                
            urn_reg = "urn.*(urn.*)\?vlan=(\d{1,4})-(urn.*)\?vlan=(\d{1,4})+.*"
            groups_reg = re.match(urn_reg, link_id)
            
            urn_src = groups_reg.group(1)
            vlan_src = groups_reg.group(2)
            urn_dst = groups_reg.group(3)
            vlan_dst = groups_reg.group(4)
            
            if urn_src not in tn_vlans:
                tn_vlans[urn_src] = set([vlan_src])
            else:
                tn_vlans[urn_src].add(vlan_src)
            if urn_dst not in tn_vlans:
                tn_vlans[urn_dst] = set([vlan_dst])
            else:
                tn_vlans[urn_dst].add(vlan_dst)
    return tn_vlans
