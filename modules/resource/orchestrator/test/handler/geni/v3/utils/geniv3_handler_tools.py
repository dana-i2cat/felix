'''
Created on Aug 1, 2014

@author: carolina
'''

import sys
sys.path.insert(0, "../../../utils")
import calls
import output_format

# TODO: Get the cert_root from the configuration settings
#cert_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../../cert"))

def handler_call(method_name, params=[], user_name="alice", arg=[]):
    if arg in ["-v", "--verbose"]:
        verbose = True
    else:
        verbose = False
    return calls.api_call(method_name, "geni/3", params=params, user_name=user_name, verbose=verbose)

def getusercred(user_cert_filename = "alice-cert.pem", geni_api = 3):
    return calls.getusercred(user_cert_filename, geni_api)

def print_call(method_name, params, res):
    return output_format.print_call(method_name, params, res)
