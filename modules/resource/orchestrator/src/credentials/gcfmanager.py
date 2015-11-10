from credentials.credentialmanagerbase import CredentialManagerBase
from core.config import ConfParser
from credentials.cred_util import CredentialVerifier
from os.path import abspath, dirname, join

import ast

class ConfigStructure:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

class GCFCredentialManager(CredentialManagerBase):
    
    def __init__(self):
        self.__abs_path = dirname(dirname(dirname(abspath(__file__))))
        self.__trusted_certs =\
            abspath(join(self.__abs_path, ast.literal_eval(ConfParser("geniv3.conf").\
                             get("certificates").get("cert_root"))))
        self.__root_cert = join(dirname(self.__trusted_certs), "server.crt")
        self.__root_cert = open(self.__root_cert, "r").read()
        self.__auth = CredentialVerifier(self.__trusted_certs)
        self.__define_config_object()
        self.__auth = CredentialVerifier(self.__config.TRUSTED_ROOTS_DIR)
        self.SFA_CREDENTIAL_TYPE = "geni_sfa"
       
    def __define_config_object(self):
        config_dict = {"TRUSTED_ROOTS_DIR": self.__trusted_certs,
                        "SFA_DATA_DIR": self.__trusted_certs,
                        "SFA_INTERFACE_HRN": "ambase",
                        "SFA_CREDENTIAL_SCHEMA": self.__root_cert,}
        self.__config = ConfigStructure(**config_dict)
 
    def get_auth(self):
        return self.__auth
    
    def get_root_cert(self):
        return self.__root_cert

    def set_auth(self, value):
        self.__auth = value
        
    def set_root_cert(self,value):
        self.__root_cert = value

    def validate_for(self, method, credentials):
        credentials = self.__clean_credentials(credentials)
        return self._get_geniv2_validation(method, credentials)
        
    def get_valid_creds(self):
        return ""

    def get_expiration_list(self, credentials):
        expirations = list()
        for cred in credentials:
            expirations.append(cred.expiration)
        return expirations

    def get_slice_expiration(self, credentials):
        return credentials[0].expiration

    def _get_geniv2_validation(self, method, credentials):
        method = (self._translate_to_geniv2_method(method),)
        try:
            valid_cred = self.__auth.verify_from_strings(self.__root_cert,credentials,None, method, {})
            return valid_cred
        except Exception as e:
            raise e
    
    def _translate_to_geniv2_method(self, method):
        if method == "Allocate" or method == "Provision":
            return "createsliver"
        elif method == "ListResources":
            return "listnodes"
        elif method == "Describe" or method == "Status":
            return "sliverstatus"
        elif method == "PerformOperationalAction":
            return "createsliver"
        elif method == "Delete":
            return "deletesliver"
        elif method == "Renew":
            return "renewsliver"
        raise Exception("Unknown method %s", method)

    def __clean_credentials(self, credentials):
        creds = list()
        for cred  in credentials:
            if cred.get("geni_value"):
                creds.append(cred["geni_value"])
            else: 
                creds.append(cred)
        return creds
