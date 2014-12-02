#!/usr/bin/env python

import sys
import os.path
import xmlrpclib
from datetime import datetime
from dateutil import parser as dateparser



# on purpose: duplicate code with geni_am_api_two_client.py
class SafeTransportWithCert(xmlrpclib.SafeTransport): 
    """Helper class to foist the right certificate for the transport class."""
    def __init__(self, key_path, cert_path):
        xmlrpclib.SafeTransport.__init__(self) # no super, because old style class
        self._key_path = key_path
        self._cert_path = cert_path
        
    def make_connection(self, host):
        """This method will automatically be called by the ServerProxy class when a transport channel is needed."""
        host_with_cert = (host, {'key_file' : self._key_path, 'cert_file' : self._cert_path})
        return xmlrpclib.SafeTransport.make_connection(self, host_with_cert) # no super, because old style class

class GENI3ClientError(Exception):
    def __init__(self, message, code):
        self._message = message
        self._code = code

    def __str__(self):
        return "%s (code: %s)" % (self._message, self._code)


class GENI3Client(object):
    """This class encapsulates a connection to a GENI AM API v3 server.
    It implements all methods of the API and manages the interaction regarding the client certificate.
    For all the client methods (e.g. listResources, describe) the given options (e.g. compress) have the default value None.
    This means if the caller does not change the value the client will not send this option and hence force the server to use the default.
    If true or false are given the options are set accordingly.
    If a time is given (e.g. end_time), please provide the method call with a Python datetime object, the RPC-conversion will then be done for you.
    
    Please also see the helper methods below.
    """
    
    RFC3339_FORMAT_STRING = '%Y-%m-%d %H:%M:%S.%fZ'
    
    def __init__(self, host, port, key_path, cert_path):
        """
        Establishes a connection proxy with the client certificate given.
        {host} e.g. 127.0.0.1
        {port} e.g. 8001
        {key_path} The file path to the client's private key.
        {cert_path} The file path to the client's certificate.
        """
        transport = SafeTransportWithCert(key_path, cert_path)
        self._proxy = xmlrpclib.ServerProxy("https://%s:%s/RPC2" % (host, str(port)), transport=transport)
    
    def getVersion(self):
        """Calls the GENI GetVersion method and returns a dict. See [geniv3rpc] GENIv3DelegateBase for more information."""
        return self._proxy.GetVersion()
        

    def listResources(self, credentials, available=None, compress=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if available != None:
            options["geni_available"] = available
        if compress != None:
            options["geni_compress"] = compress
        return self._proxy.ListResources(credentials, options)
    
    def describe(self, urns, credentials, compress=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if compress != None:
            options["geni_compress"] = compress
        return self._proxy.ListResources(credentials, options)
            
    def allocate(self, slice_urn, credentials, rspec, end_time=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if end_time != None:
            options["geni_end_time"] = self.datetime2str(end_time)
        return self._proxy.Allocate(slice_urn, credentials, rspec, options)
    
    def renew(self, urns, credentials, expiration_time, best_effort=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if best_effort != None:
            options["geni_best_effort"] = best_effort
        return self._proxy.Renew(urns, credentials, self.datetime2str(expiration_time), options)
        
    def provision(self, urns, credentials, best_effort=None, end_time=None, users=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if best_effort != None:
            options["geni_best_effort"] = best_effort
        if end_time != None:
            options["geni_end_time"] = self.datetime2str(end_time)
        if users != None:
            options["geni_users"] = users
        return self._proxy.Provision(urns, credentials, options)

    def status(self, urns, credentials):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        return self._proxy.Status(urns, credentials, options)
        
    def performOperationalAction(self, urns, credentials, action, best_effort=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if best_effort != None:
            options["geni_best_effort"] = best_effort
        return self._proxy.PerformOperationalAction(urns, credentials, action, options)
        
    def delete(self, urns, credentials, best_effort=None):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        if best_effort != None:
            options["geni_best_effort"] = best_effort
        return self._proxy.Delete(urns, credentials, options)

    def shutdown(self, slice_urn, credentials):
        """See class description above and the [geniv3rpc] GENIv3DelegateBase for more information."""
        options = self._default_options()
        return self._proxy.Shutdown(slice_urn, credentials, options)

    def _default_options(self):
        """Private method for generating the default option hash, which is parsed on the server."""
        return {"geni_rspec_version" : {"version" : 3, "type" : "geni"}}

    # helper methods
    def datetime2str(self, dt):
        """Convers a datetime to a string which can be parsed by the GENI AM API server."""
        return dt.strftime(self.RFC3339_FORMAT_STRING)
    def str2datetime(self, strval):
        """Coverts a date string given by the GENI AM API server to a python datetime object.
        It parses the given date string and converts the timestamp to utc and the date unaware of timezones."""
        result = dateparser.parse(strval)
        if result:
            result = result - result.utcoffset()
            result = result.replace(tzinfo=None)
        return result

    def raiseIfError(self, response):
        """Raises an GENI3ClientError if the server response contained an error."""
        if self.isError(response):
            raise GENI3ClientError(self.errorMessage(response), self.errorCode(response))
        return

    def errorMessage(self, response):
        return response['output']
    def errorCode(self, response):
        return int(response['code']['geni_code'])
    def isError(self, response):
        return self.errorCode(response) != 0
        

# Test code

TEST_SLICE_URN = 'urn:publicid:IDN+test.fp7-ofelia.eu+slice+pizzaslice'
# to get a request rspec call listResources on the AM, select the resources you want and change the rspec-type to "request"
TEST_REQUEST_RSPEC = '<?xml version="1.0" encoding="UTF-8"?><rspec type="request" xmlns="http://www.geni.net/resources/rspec/3" xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" xmlns:dhcp="http://example.com/dhcp" xs:schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/ad.xsd http://example.com/dhcp/req.xsd"><dhcp:ip>192.168.1.1</dhcp:ip><dhcp:ip>192.168.1.2</dhcp:ip><dhcp:iprange><from>192.168.1.3</from><to>192.168.1.6</to></dhcp:iprange></rspec>'

if __name__ == '__main__':
    # get the right paths together
    local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'creds'))
    key_path = os.path.join(local_path, "alice-key.pem") # make sure the CA of the AM is the same which issued this certificate (e.g. copy certificates from omni)
    cert_path = os.path.join(local_path, "alice-cert.pem")
    
    # instanciate the client
    client = GENI3Client('127.0.0.1', 8001, key_path, cert_path)
    
    # load test credential (look into the `test/creds/TODO.md` to generate these certs)
    with open(os.path.join(local_path, "alice-cred.xml"), 'r') as f:
        TEST_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}
    with open(os.path.join(local_path, "pizzaslice_cred.xml"), 'r') as f:
        TEST_SLICE_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}

    # all method calls
    print client.listResources([TEST_CREDENTIAL], True, False)
    # print client.describe(TEST_SLICE_URN, [TEST_SLICE_CREDENTIAL], False)
    # print client.allocate(TEST_SLICE_URN, [TEST_SLICE_CREDENTIAL], TEST_REQUEST_RSPEC, datetime.now())
    # print client.renew([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL], datetime.now(), best_effort=True)
    # print client.provision([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL], best_effort=True, end_time= datetime.now())
    # print client.status([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
    # print client.performOperationalAction([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL], "geni_start")
    # print client.delete([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
    # print client.shutdown([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
    
    # simple error handling
    # response = client.shutdown([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
    # client.raiseIfError(response)
    
    # catch error the error
    # try:
    #     response = client.shutdown([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
    #     client.raiseIfError(response)
    # except GENI3ClientError as e:
    #     print str(e)
    