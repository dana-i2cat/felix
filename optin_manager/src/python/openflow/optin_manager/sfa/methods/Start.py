from openflow.optin_manager.sfa.util.xrn import urn_to_hrn
from openflow.optin_manager.sfa.trust.credential import Credential
from openflow.optin_manager.sfa.trust.auth import Auth

class Start:
    
    def __init__(self, xrn, creds, **kwargs):
        hrn, type = urn_to_hrn(xrn)
        valid_creds = Auth().checkCredentials(creds, 'startslice', hrn)
        origin_hrn = Credential(string=valid_creds[0]).get_gid_caller().get_hrn()

 
        return  
