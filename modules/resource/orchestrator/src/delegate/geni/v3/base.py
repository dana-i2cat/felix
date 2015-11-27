from core.config import FullConfParser
from handler.geni.v3 import exceptions
from lxml import etree
from lxml.builder import ElementMaker

from core import log
logger=log.getLogger('geniv3delegatebase')

import ast
import extensions
import os
import urllib2


class GENIv3DelegateBase(object):
    """
    Please find more information about the concept of Handlers and Delegates via the wiki (e.g. https://github.com/motine/AMsoil/wiki/GENI).

    The GENIv3 handler (see above) assumes that this class uses RSpec version 3 when interacting with the client.
    For creating new a new RSpec type/extension, please see the wiki via https://github.com/motine/AMsoil/wiki/RSpec.

    General parameters for all following methods:
    {client_cert} The client's certificate. See [flaskrpcs]XMLRPCDispatcher.requestCertificate(). Also see http://groups.geni.net/geni/wiki/GeniApiCertificates
    {credentials} The a list of credentials in the format specified at http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#credentials

    Dates are converted to UTC and then made timezone-unaware (see http://docs.python.org/2/library/datetime.html#datetime.datetime.astimezone).
    """

    ALLOCATION_STATE_UNALLOCATED = 'geni_unallocated'
    """The sliver does not exist. (see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#SliverAllocationStates)"""
    ALLOCATION_STATE_ALLOCATED = 'geni_allocated'
    """The sliver is offered/promissed, but it does not consume actual resources. This state shall time out at some point in time."""
    ALLOCATION_STATE_PROVISIONED = 'geni_provisioned'
    """The sliver is/has been instanciated. Operational states apply here."""

    OPERATIONAL_STATE_PENDING_ALLOCATION = 'geni_pending_allocation'
    """Required for aggregates to support. A transient state."""
    OPERATIONAL_STATE_NOTREADY           = 'geni_notready'
    """Optional. A stable state."""
    OPERATIONAL_STATE_CONFIGURING        = 'geni_configuring'
    """Optional. A transient state."""
    OPERATIONAL_STATE_STOPPING           = 'geni_stopping'
    """Optional. A transient state."""
    OPERATIONAL_STATE_READY              = 'geni_ready'
    """Optional. A stable state."""
    OPERATIONAL_STATE_READY_BUSY         = 'geni_ready_busy'
    """Optional. A transient state."""
    OPERATIONAL_STATE_FAILED             = 'geni_failed'
    """Optional. A stable state."""

    OPERATIONAL_ACTION_START   = 'geni_start'
    """Sliver shall become geni_ready. The AM developer may define more states (see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#SliverOperationalActions)"""
    OPERATIONAL_ACTION_RESTART = 'geni_restart'
    """Sliver shall become geni_ready again."""
    OPERATIONAL_ACTION_STOP    = 'geni_stop'
    """Sliver shall become geni_notready."""
    OPERATIONAL_ACTION_UPDATE_USERS    = 'geni_update_users'
    OPERATIONAL_ACTION_UPDATING_USERS_CANCEL    = 'geni_updating_users_cancel'
    """
    Following operational actions not fully implemented.
    """
    OPERATIONAL_ACTION_CONSOLE_URL    = 'geni_console_url'
    OPERATIONAL_ACTION_SHARELAN    = 'geni_sharelan'
    OPERATIONAL_ACTION_UNSHARELAN    = 'geni_unsharelan'

    def __init__(self):
        super(GENIv3DelegateBase, self).__init__()
        self.config = FullConfParser()
        self.general_section = self.config.get("geniv3.conf").get("general")
        self.certificates_section = self.config.get("auth.conf").get("certificates")

    def get_request_extensions_list(self):
        """Not to overwrite by AM developer. Should retrun a list of request extensions (XSD schemas) to be sent back by GetVersion."""
        return [uri for prefix, uri in self.get_request_extensions_mapping().items()]
    def get_request_extensions_mapping(self):
        """Overwrite by AM developer. Should return a dict of namespace names and request extensions (XSD schema's URLs as string).
        Format: {xml_namespace_prefix : namespace_uri, ...}
        """
        return {}

    def get_manifest_extensions_mapping(self):
        """Overwrite by AM developer. Should return a dict of namespace names and manifest extensions (XSD schema's URLs as string).
        Format: {xml_namespace_prefix : namespace_uri, ...}
        """
        return {}

    def get_ad_extensions_list(self):
        """Not to overwrite by AM developer. Should retrun a list of request extensions (XSD schemas) to be sent back by GetVersion."""
        return [uri for prefix, uri in self.get_ad_extensions_mapping().items()]
    def get_ad_extensions_mapping(self):
        """Overwrite by AM developer. Should return a dict of namespace names and advertisement extensions (XSD schema URLs as string) to be sent back by GetVersion.
        Format: {xml_namespace_prefix : namespace_uri, ...}
        """
        return {}

    def is_single_allocation(self):
        """Overwrite by AM developer. Shall return a True or False. When True (not default), and performing one of (Describe, Allocate, Renew, Provision, Delete), such an AM requires you to include either the slice urn or the urn of all the slivers in the same state.
        see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#OperationsonIndividualSlivers"""
        return False

    def get_allocation_mode(self):
        """Overwrite by AM developer. Shall return a either 'geni_single', 'geni_disjoint', 'geni_many'.
        It defines whether this AM allows adding slivers to slices at an AM (i.e. calling Allocate multiple times, without first deleting the allocated slivers).
        For description of the options see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#OperationsonIndividualSlivers"""
        return 'geni_single'

    def list_resources(self, client_cert, credentials, geni_available):
        """Overwrite by AM developer. Shall return an RSpec version 3 (advertisement) or raise an GENIv3...Error.
        If {geni_available} is set, only return availabe resources.
        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#ListResources"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def describe(self, urns, client_cert, credentials):
        """Overwrite by AM developer. Shall return an RSpec version 3 (manifest) or raise an GENIv3...Error.
        {urns} contains a list of slice identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).

        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Describe"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def allocate(self, slice_urn, client_cert, credentials, rspec, end_time=None):
        """Overwrite by AM developer.
        Shall return the two following values or raise an GENIv3...Error.
        - a RSpec version 3 (manifest) of newly allocated slivers
        - a list of slivers of the format:
            [{'geni_sliver_urn' : String,
              'exceptionspires'    : Python-Date,
              'geni_allocation_status' : one of the ALLOCATION_STATE_xxx},
             ...]
        Please return like so: "return respecs, slivers"
        {slice_urn} contains a slice identifier (e.g. 'urn:publicid:IDN+ofelia:eict:gcf+slice+myslice').
        {end_time} Optional. A python datetime object which determines the desired expiry date of this allocation (see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#geni_end_time).
        >>> This is the first part of what CreateSliver used to do in previous versions of the AM API. The second part is now done by Provision, and the final part is done by PerformOperationalAction.

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Allocate"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def renew(self, urns, client_cert, credentials, expiration_time, best_effort):
        """Overwrite by AM developer.
        Shall return a list of slivers of the following format or raise an GENIv3...Error:
            [{'geni_sliver_urn'         : String,
              'geni_allocation_status'  : one of the ALLOCATION_STATE_xxx,
              'geni_operational_status' : one of the OPERATIONAL_STATE_xxx,
              'exceptionspires'            : Python-Date,
              'geni_error'              : optional String},
             ...]

        {urns} contains a list of slice identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).
        {expiration_time} is a python datetime object
        {best_effort} determines if the method shall fail in case that not all of the urns can be renewed (best_effort=False).

        If the transactional behaviour of {best_effort}=False can not be provided, throw a GENIv3OperationUnsupportedError.
        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Renew"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def provision(self, urns, client_cert, credentials, best_effort, end_time, geni_users):
        """Overwrite by AM developer.
        Shall return the two following values or raise an GENIv3...Error.
        - a RSpec version 3 (manifest) of slivers
        - a list of slivers of the format:
            [{'geni_sliver_urn'         : String,
              'geni_allocation_status'  : one of the ALLOCATION_STATE_xxx,
              'geni_operational_status' : one of the OPERATIONAL_STATE_xxx,
              'exceptionspires'            : Python-Date,
              'geni_error'              : optional String},
             ...]
        Please return like so: "return respecs, slivers"

        {urns} contains a list of slice/resource identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).
        {best_effort} determines if the method shall fail in case that not all of the urns can be provisioned (best_effort=False)
        {end_time} Optional. A python datetime object which determines the desired expiry date of this provision (see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#geni_end_time).
        {geni_users} is a list of the format: [ { 'urn' : ..., 'keys' : [sshkey, ...]}, ...]

        If the transactional behaviour of {best_effort}=False can not be provided, throw a GENIv3OperationUnsupportedError.
        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Provision"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def status(self, urns, client_cert, credentials):
        """Overwrite by AM developer.
        Shall return the two following values or raise an GENIv3...Error.
        - a slice urn
        - a list of slivers of the format:
            [{'geni_sliver_urn'         : String,
              'geni_allocation_status'  : one of the ALLOCATION_STATE_xxx,
              'geni_operational_status' : one of the OPERATIONAL_STATE_xxx,
              'exceptionspires'            : Python-Date,
              'geni_error'              : optional String},
             ...]
        Please return like so: "return slice_urn, slivers"

        {urns} contains a list of slice/resource identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).
        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Status"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def perform_operational_action(self, urns, client_cert, credentials, action, best_effort):
        """Overwrite by AM developer.
        Shall return a list of slivers of the following format or raise an GENIv3...Error:
            [{'geni_sliver_urn'         : String,
              'geni_allocation_status'  : one of the ALLOCATION_STATE_xxx,
              'geni_operational_status' : one of the OPERATIONAL_STATE_xxx,
              'exceptionspires'            : Python-Date,
              'geni_error'              : optional String},
             ...]

        {urns} contains a list of slice or sliver identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).
        {action} an arbitraty string, but the following should be possible: "geni_start", "geni_stop", "geni_restart"
        {best_effort} determines if the method shall fail in case that not all of the urns can be changed (best_effort=False)

        If the transactional behaviour of {best_effort}=False can not be provided, throw a GENIv3OperationUnsupportedError.
        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#PerformOperationalAction"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def delete(self, urns, client_cert, credentials, best_effort):
        """Overwrite by AM developer.
        Shall return a list of slivers of the following format or raise an GENIv3...Error:
            [{'geni_sliver_urn'         : String,
              'geni_allocation_status'  : one of the ALLOCATION_STATE_xxx,
              'exceptionspires'            : Python-Date,
              'geni_error'              : optional String},
             ...]

        {urns} contains a list of slice/resource identifiers (e.g. ['urn:publicid:IDN+ofelia:eict:gcf+slice+myslice']).
        {best_effort} determines if the method shall fail in case that not all of the urns can be deleted (best_effort=False)

        If the transactional behaviour of {best_effort}=False can not be provided, throw a GENIv3OperationUnsupportedError.
        For more information on possible {urns} see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#urns

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Delete"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def shutdown(self, slice_urn, client_cert, credentials):
        """Overwrite by AM developer.
        Shall return True or False or raise an GENIv3...Error.

        For full description see http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Shutdown"""
        raise exceptions.GENIv3GeneralError("Method not implemented yet")

    def auth(self, client_cert, credentials, slice_urn=None, privileges=()):
        """
        This method authenticates and authorizes.
        It returns the client's urn, uuid, email (extracted from the {client_cert}). Example call: "urn, uuid, email = self.auth(...)"
        Be aware, the email is not required in the certificate, hence it might be empty.
        If the validation fails, an GENIv3ForbiddenError is thrown.

        The credentials are checked so the user has all the required privileges (success if any credential fits all privileges).
        The client certificate is not checked: this is usually done via the webserver configuration.
        This method only treats certificates of type 'geni_sfa'.

        Here a list of possible privileges (format: right_in_credential: [privilege1, privilege2, ...]):
            "authority" : ["register", "remove", "update", "resolve", "list", "getcredential", "*"],
            "refresh"   : ["remove", "update"],
            "resolve"   : ["resolve", "list", "getcredential"],
            "sa"        : ["getticket", "redeemslice", "redeemticket", "createslice", "createsliver", "deleteslice", "deletesliver", "updateslice",
                           "getsliceresources", "getticket", "loanresources", "stopslice", "startslice", "renewsliver",
                            "deleteslice", "deletesliver", "resetslice", "listslices", "listnodes", "getpolicy", "sliverstatus"],
            "embed"     : ["getticket", "redeemslice", "redeemticket", "createslice", "createsliver", "renewsliver", "deleteslice",
                           "deletesliver", "updateslice", "sliverstatus", "getsliceresources", "shutdown"],
            "bind"      : ["getticket", "loanresources", "redeemticket"],
            "control"   : ["updateslice", "createslice", "createsliver", "renewsliver", "sliverstatus", "stopslice", "startslice",
                           "deleteslice", "deletesliver", "resetslice", "getsliceresources", "getgids"],
            "info"      : ["listslices", "listnodes", "getpolicy"],
            "ma"        : ["setbootstate", "getbootstate", "reboot", "getgids", "gettrustedcerts"],
            "operator"  : ["gettrustedcerts", "getgids"],
            "*"         : ["createsliver", "deletesliver", "sliverstatus", "renewsliver", "shutdown"]

        When using the gcf clearinghouse implementation the credentials will have the rights:
        - user: "refresh", "resolve", "info" (which resolves to the privileges: "remove", "update", "resolve", "list", "getcredential", "listslices", "listnodes", "getpolicy").
        - slice: "refresh", "embed", "bind", "control", "info" (well, do the resolving yourself...)
        """
        # check variables
        if not isinstance(privileges, tuple):
            raise TypeError("Privileges need to be a tuple.")
        # collect credentials (only GENI certs, version ignored)
        geni_credentials = []
        for c in credentials:
            if c['geni_type'] == 'geni_sfa':
                geni_credentials.append(c['geni_value'])

        # Get the cert_root from the configuration settings
        root_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../../"))
        cert_root = os.path.join(root_path, self.certificates_section.get("cert_root"))
        logger.debug("client_certificate trusted, present at: %s" % str(cert_root))
        logger.debug("client_certificate:\n%s" % str(client_cert))

        if client_cert == None:
            raise exceptions.GENIv3ForbiddenError("Could not determine the client SSL certificate")
        # test the credential
        try:
            cred_verifier = extensions.geni.util.cred_util.CredentialVerifier(cert_root)
            cred_verifier.verify_from_strings(client_cert, geni_credentials, slice_urn, privileges)
        except Exception as e:
            raise exceptions.GENIv3ForbiddenError(str(e))

        user_gid = extensions.sfa.trust.gid.GID(string=client_cert)
        user_urn = user_gid.get_urn()
        user_uuid = user_gid.get_uuid()
        user_email = user_gid.get_email()
        return user_urn, user_uuid, user_email # TODO document return

    def urn_type(self, urn):
        """Returns the type of the urn (e.g. slice, sliver).
        For the possible types see: http://groups.geni.net/geni/wiki/GeniApiIdentifiers#ExamplesandUsage"""
        return urn.split('+')[2].strip()

    def lxml_ad_root(self):
        """Returns a xml root node with the namespace extensions specified by self.get_ad_extensions_mapping."""
        return etree.Element('rspec', self.get_ad_extensions_mapping(), type='advertisement')

    def lxml_manifest_root(self):
        """Returns a xml root node with the namespace extensions specified by self.get_manifest_extensions_mapping."""
        return etree.Element('rspec', self.get_manifest_extensions_mapping(), type='manifest')

    def lxml_to_string(self, rspec):
        """Converts a lxml root node to string (for returning to the client)."""
        return etree.tostring(rspec, pretty_print=True)

    def lxml_ad_element_maker(self, prefix):
        """Returns a lxml.builder.ElementMaker configured for avertisements and the namespace given by {prefix}."""
        ext = self.get_ad_extensions_mapping()
        return ElementMaker(namespace=ext[prefix], nsmap=ext)

    def lxml_manifest_element_maker(self, prefix):
        """Returns a lxml.builder.ElementMaker configured for manifests and the namespace given by {prefix}."""
        ext = self.get_manifest_extensions_mapping()
        return ElementMaker(namespace=ext[prefix], nsmap=ext)

    def lxml_parse_rspec(self, rspec_string):
        """Returns a the root element of the given {rspec_string} as lxml.Element.
        If the config key is set, the rspec is validated with the schemas found at the URLs specified in schemaLocation of the the given RSpec."""
        # parse
        rspec_root = etree.fromstring(rspec_string)
        # validate RSpec against specified schemaLocations
        should_validate = ast.literal_eval(self.general_section.get("rspec_validation"))

        if should_validate:
            schema_locations = rspec_root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation")
            if schema_locations:
                schema_location_list = schema_locations.split(" ")
                schema_location_list = map(lambda x: x.strip(), schema_location_list) # strip whitespaces
                for sl in schema_location_list:
                    try:
                        xmlschema_contents = urllib2.urlopen(sl) # try to download the schema
                        xmlschema_doc = etree.parse(xmlschema_contents)
                        xmlschema = etree.XMLSchema(xmlschema_doc)
                        xmlschema.validate(rspec_root)
                    except Exception as e:
                        logger.warning("RSpec validation failed failed (%s: %s)" % (sl, str(e),))
            else:
                logger.warning("RSpec does not specify any schema locations")
        return rspec_root

    def lxml_elm_has_request_prefix(self, lxml_elm, ns_name):
        return str(lxml_elm.tag).startswith("{%s}" % (self.get_request_extensions_mapping()[ns_name],))

    def lxml_elm_equals_request_tag(self, lxml_elm, ns_name, tagname):
        """Determines if the given tag by {ns_name} and {tagname} equals lxml_tag. The namespace URI is looked up via get_request_extensions_mapping()['ns_name']"""
        return ("{%s}%s" % (self.get_request_extensions_mapping()[ns_name], tagname)) == str(lxml_elm.tag)
