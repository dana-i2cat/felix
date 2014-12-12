#----------------------------------------------------------------------
# Copyright (c) 2008 Board of Trustees, Princeton University
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS 
# IN THE WORK.
#----------------------------------------------------------------------
##
# Implements SFA GID. GIDs are based on certificates, and the GID class is a
# descendant of the certificate class.
##

### $Id$
### $URL$
import xmlrpclib
import uuid
from expedient.common.federation.sfa.trust.certificate import Certificate
from expedient.common.federation.sfa.util.namespace import *
from expedient.common.federation.sfa.util.sfalogging import logger
import datetime as dt
from dateutil import tz
##
# Create a new uuid. Returns the UUID as a string.

def create_uuid():
    return str(uuid.uuid4().int)

##
# GID is a tuple:
#    (uuid, urn, public_key)
#
# UUID is a unique identifier and is created by the python uuid module
#    (or the utility function create_uuid() in gid.py).
#
# HRN is a human readable name. It is a dotted form similar to a backward domain
#    name. For example, planetlab.us.arizona.bakers.
#
# URN is a human readable identifier of form:
#   "urn:publicid:IDN+toplevelauthority[:sub-auth.]*[\res. type]\ +object name"
#   For  example, urn:publicid:IDN+planetlab:us:arizona+user+bakers      
#
# PUBLIC_KEY is the public key of the principal identified by the UUID/HRN.
# It is a Keypair object as defined in the cert.py module.
#
# It is expected that there is a one-to-one pairing between UUIDs and HRN,
# but it is uncertain how this would be inforced or if it needs to be enforced.
#
# These fields are encoded using xmlrpc into the subjectAltName field of the
# x509 certificate. Note: Call encode() once the fields have been filled in
# to perform this encoding.


class GID(Certificate):
    uuid = None
    hrn = None
    urn = None

    ##
    # Create a new GID object
    #
    # @param create If true, create the X509 certificate
    # @param subject If subject!=None, create the X509 cert and set the subject name
    # @param string If string!=None, load the GID from a string
    # @param filename If filename!=None, load the GID from a file

    def __init__(self, create=False, subject=None, string=None, filename=None, uuid=None, hrn=None, urn=None):
        
        Certificate.__init__(self, create, subject, string, filename)
        if subject:
            logger.debug("Creating GID for subject: %s" % subject)
        if uuid:
            self.uuid = int(uuid)
        if hrn:
            self.hrn = hrn
            self.urn = hrn_to_urn(hrn, 'unknown')
        if urn:
            self.urn = urn
            self.hrn, type = urn_to_hrn(urn)

    def set_uuid(self, uuid):
        if isinstance(uuid, str):
            self.uuid = int(uuid)
        else:
            self.uuid = uuid

    def get_uuid(self):
        if not self.uuid:
            self.decode()
        return self.uuid

    def set_hrn(self, hrn):
        self.hrn = hrn

    def get_hrn(self):
        if not self.hrn:
            self.decode()
        return self.hrn

    def set_urn(self, urn):
        self.urn = urn
        self.hrn, type = urn_to_hrn(urn)
 
    def get_urn(self):
        if not self.urn:
            self.decode()
        return self.urn            

    def get_type(self):
        if not self.urn:
            self.decode()
        _, t = urn_to_hrn(self.urn)
        return t
    
    ##
    # Encode the GID fields and package them into the subject-alt-name field
    # of the X509 certificate. This must be called prior to signing the
    # certificate. It may only be called once per certificate.

    def encode(self):
        if self.urn:
            urn = self.urn
        else:
            urn = hrn_to_urn(self.hrn, None)
            
        str = "URI:" + urn

        if self.uuid:
            str += ", " + "URI:" + uuid.UUID(int=self.uuid).urn
        
        self.set_data(str, 'subjectAltName')

        


    ##
    # Decode the subject-alt-name field of the X509 certificate into the
    # fields of the GID. This is automatically called by the various get_*()
    # functions in this class.

    def decode(self):
        data = self.get_data('subjectAltName')
        dict = {}
        if data:
            if data.lower().startswith('uri:http://<params>'):
                dict = xmlrpclib.loads(data[11:])[0][0]
            else:
                spl = data.split(', ')
                for val in spl:
                    if val.lower().startswith('uri:urn:uuid:'):
                        dict['uuid'] = uuid.UUID(val[4:]).int
                    elif val.lower().startswith('uri:urn:publicid:idn+'):
                        dict['urn'] = val[4:]
                    
        self.uuid = dict.get("uuid", None)
        self.urn = dict.get("urn", None)
        self.hrn = dict.get("hrn", None)    
        if self.urn:
            self.hrn = urn_to_hrn(self.urn)[0]

    ##
    # Dump the credential to stdout.
    #
    # @param indent specifies a number of spaces to indent the output
    # @param dump_parents If true, also dump the parents of the GID

    def dump(self, indent=0, dump_parents=False):
        print " "*indent, " hrn:", self.get_hrn()
        print " "*indent, " urn:", self.get_urn()
        print " "*indent, "uuid:", self.get_uuid()

        if self.parent and dump_parents:
            print " "*indent, "parent:"
            self.parent.dump(indent+4, dump_parents)

    ##
    # Verify the chain of authenticity of the GID. First perform the checks
    # of the certificate class (verifying that each parent signs the child,
    # etc). In addition, GIDs also confirm that the parent's HRN is a prefix
    # of the child's HRN.
    #
    # Verifying these prefixes prevents a rogue authority from signing a GID
    # for a principal that is not a member of that authority. For example,
    # planetlab.us.arizona cannot sign a GID for planetlab.us.princeton.foo.

    def verify_chain(self, trusted_certs = None):
        # do the normal certificate verification stuff
        trusted_root = Certificate.verify_chain(self, trusted_certs)        
       
        if self.parent:
            # make sure the parent's hrn is a prefix of the child's hrn
            if not self.get_hrn().startswith(self.parent.get_hrn()):
                #print self.get_hrn(), " ", self.parent.get_hrn()
                raise GidParentHrn("This cert %s HRN doesnt start with parent HRN %s" % (self.get_hrn(), self.parent.get_hrn()))
        else:
            # make sure that the trusted root's hrn is a prefix of the child's
            trusted_gid = GID(string=trusted_root.save_to_string())
            trusted_type = trusted_gid.get_type()
            trusted_hrn = trusted_gid.get_hrn()
            #if trusted_type == 'authority':
            #    trusted_hrn = trusted_hrn[:trusted_hrn.rindex('.')]
            cur_hrn = self.get_hrn()
            if not self.get_hrn().startswith(trusted_hrn):
                raise GidParentHrn("Trusted roots HRN %s isnt start of this cert %s" % (trusted_hrn, cur_hrn))

        return

    def get_notBefore(self):
        str_val = self.cert.get_notBefore()
        utc = dt.datetime.strptime(str_val,'%Y%m%d%H%M%SZ')
        return utc.strftime('%I:%M %p, %d %B %Y (GMT)')

    def get_notAfter(self):
        str_val = self.cert.get_notAfter()
        utc = dt.datetime.strptime(str_val,'%Y%m%d%H%M%SZ')
        return utc.strftime('%I:%M %p, %d %B %Y (GMT)')
