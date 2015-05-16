# commented out the unused modules

# import os, os.path
# import urllib2
import traceback
from datetime import datetime
from dateutil import parser as dateparser
import base64
import zlib

# from lxml import etree
# from lxml.builder import ElementMaker

from handler.geni.v3 import exceptions as geni_ex
# import handler.geni.v3.extensions.geni
# import handler.geni.v3.extensions.sfa.trust.gid as gid

from core import log
logger = log.getLogger("handlergeniv3")

# import ast

from server.flask.flaskserver import FlaskServer
# Create and register the RPC server
flaskserver = FlaskServer()
from server.flask.flaskxmlrpc import FlaskXMLRPC
xmlrpc = FlaskXMLRPC(flaskserver)
#from SimpleXMLRPCServer import SimpleXMLRPCDispatcher as Dispatcher


class GENIv3Handler(xmlrpc.Dispatcher):
    RFC3339_FORMAT_STRING = "%Y-%m-%d %H:%M:%S.%fZ"

    def __init__(self):
        super(GENIv3Handler, self).__init__(logger)
        self._delegate = None

    def setDelegate(self, geniv3delegate):
        self._delegate = geniv3delegate

    def getDelegate(self):
        return self._delegate

    # RSPEC3_NAMESPACE= "http://www.geni.net/resources/rspec/3"

    def GetVersion(self):
        """Returns the version of this interface.
        This method can be hard coded, since we are actually setting up the
        GENI v3 API, only. For the RSpec extensions, we ask the delegate."""
        # no authentication necessary

        # TODO: Move to delegate and dispatch requests there
        try:
            request_extensions = self._delegate.get_request_extensions_list()
            ad_extensions = self._delegate.get_ad_extensions_list()
            allocation_mode = self._delegate.get_allocation_mode()
            is_single_allocation = self._delegate.is_single_allocation()

        except Exception as e:
            return self._errorReturn(e)

        request_rspec_versions = [
            {"type": "geni", "version": 3,
             "schema": "http://www.geni.net/resources/rspec/3/request.xsd",
             "namespace": "http://www.geni.net/resources/rspec/3",
#             "extensions": request_extensions,
             "extensions": [],
            },
        ]
        ad_rspec_versions = [
            {"type": "geni", "version": 3,
             "schema": "http://www.geni.net/resources/rspec/3/ad.xsd",
             "namespace": "http://www.geni.net/resources/rspec/3",
#             "extensions": ad_extensions,
             "extensions": [],
            },
        ]
        credential_types = [ {"geni_type": "geni_sfa", "geni_version": 3} ]

        return self._successReturn(
            {"geni_api": 3,
             "geni_api_versions": {"3": "/xmlrpc/geni/3/"},  # should be absolute URL
             "geni_request_rspec_versions": request_rspec_versions,
             "geni_ad_rspec_versions": ad_rspec_versions,
             "geni_credential_types": credential_types,
#             "geni_single_allocation": is_single_allocation,
#             "geni_allocate": allocation_mode})
            })

    def ListResources(self, credentials, options):
        """Delegates the call and unwraps the needed parameter.
        Also takes care of the compression option."""
        # interpret options
        geni_available = self._option(options, "geni_available")
        geni_compress = self._option(options, "geni_compressed")

        # check version and delegate
        try:
            self._checkRSpecVersion(options["geni_rspec_version"])
            result = self._delegate.list_resources(self.requestCertificate(),
                                                   credentials, geni_available)
        except Exception as e:
            return self._errorReturn(e)

        # compress and return
        if geni_compress:
            result = base64.b64encode(zlib.compress(result))

        return self._successReturn(result)

    def Describe(self, urns, credentials, options):
        """Delegates the call and unwraps the needed parameter.
        Also takes care of the compression option."""
        # some duplication with above
        geni_compress = self._option(options, "geni_compressed")

        try:
            self._checkRSpecVersion(options["geni_rspec_version"])
            result = self._delegate.describe(urns, self.requestCertificate(),
                                             credentials)
        except Exception as e:
            return self._errorReturn(e)

        if geni_compress:
            result = base64.b64encode(zlib.compress(result))

        return self._successReturn(result)

    def Allocate(self, slice_urn, credentials, rspec, options):
        """Delegates the call and unwraps the needed parameter.
        Also converts the incoming timestamp to python and the outgoing
        to geni compliant date format."""
        geni_end_time = None
        if "geni_end_time" in options:
            geni_end_time = self._str2datetime(options["geni_end_time"])

        # TODO check the end_time against the duration of the credential
        try:
            # delegate
            # omni does not send this option
            # self._checkRSpecVersion(options["geni_rspec_version"])
            r_rspec, r_sliver_list = self._delegate.allocate(
                slice_urn, self.requestCertificate(),
                credentials, rspec, geni_end_time)

            # change datetime"s to strings
            result = {"geni_rspec": r_rspec,
                      "geni_slivers": self._convertExpiresDate(r_sliver_list)}

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Renew(self, urns, credentials, expiration_time_str, options):
        geni_best_effort = self._option(options, "geni_best_effort", ret=True)
        expiration_time = self._str2datetime(expiration_time_str)
        try:
            # delegate
            result = self._delegate.renew(urns, self.requestCertificate(),
                                          credentials, expiration_time,
                                          geni_best_effort)
            # change datetime"s to strings
            result = self._convertExpiresDate(result)

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Provision(self, urns, credentials, options):
        geni_best_effort = self._option(options, "geni_best_effort", ret=True)
        geni_users = self._option(options, "geni_users", ret=[])
        geni_end_time = None
        if "geni_end_time" in options:
            geni_end_time = self._str2datetime(options["geni_end_time"])

        # TODO check the end_time against the duration of the credential
        try:
            self._checkRSpecVersion(options["geni_rspec_version"])
            r_rspec, r_sliver_list = self._delegate.provision(
                urns, self.requestCertificate(), credentials, geni_best_effort,
                geni_end_time, geni_users)

            result = {"geni_rspec": r_rspec,
                      "geni_slivers": self._convertExpiresDate(r_sliver_list)}

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Status(self, urns, credentials, options):
        try:
            r_sliceurn, r_sliver_list = self._delegate.status(
                urns, self.requestCertificate(), credentials)

            result = {"geni_urn": r_sliceurn,
                      "geni_slivers": self._convertExpiresDate(r_sliver_list)}

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def PerformOperationalAction(self, urns, credentials, action, options):
        geni_best_effort = self._option(options, "geni_best_effort")
        try:
            result = self._delegate.perform_operational_action(
                urns, self.requestCertificate(), credentials,
                action, geni_best_effort)

            result = self._convertExpiresDate(result)

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Delete(self, urns, credentials, options):
        geni_best_effort = self._option(options, "geni_best_effort")
        try:
            result = self._delegate.delete(urns,
                                           self.requestCertificate(),
                                           credentials, geni_best_effort)

            result = self._convertExpiresDate(result)

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Shutdown(self, slice_urn, credentials, options):
        try:
            result = bool(self._delegate.shutdown(slice_urn,
                                                  self.requestCertificate(),
                                                  credentials))
        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    # ---- helper methods
    def _datetime2str(self, dt):
        return dt.strftime(self.RFC3339_FORMAT_STRING)

    def _str2datetime(self, strval):
        """Parses the given date string and converts the timestamp
        to utc and the date unaware of timezones."""
        result = dateparser.parse(strval)
        if result:
            result = result - result.utcoffset()
            result = result.replace(tzinfo=None)

        return result

    def _convertExpiresDate(self, sliver_list):
        for slhash in sliver_list:
            if slhash["geni_expires"] is None:
                continue

            if not isinstance(slhash["geni_expires"], datetime):
                raise ValueError("Given geni_expires in sliver_list hash " +
                                 "retrieved from delegate's method is not " +
                                 "a python datetime object.")

            slhash["geni_expires"] = self._datetime2str(slhash["geni_expires"])

        return sliver_list

    def _checkRSpecVersion(self, rspec_version_option):
        if (int(rspec_version_option["version"]) != 3) or\
           (rspec_version_option["type"].lower() != "geni"):
            raise geni_ex.GENIv3BadArgsError("Only RSpec 3 supported.")

    def _errorReturn(self, e):
        """Assembles a GENI compliant return result for faulty methods."""
        # convert common errors into GENIv3GeneralError
        if not isinstance(e, geni_ex.GENIv3BaseError):
            e = geni_ex.GENIv3ServerError(str(e))

        # do some logging
        logger.error(e)
        logger.error(traceback.format_exc())
        return {"geni_api": 3,
                "code": {"geni_code": e.code}, "output": str(e)}

    def _successReturn(self, result):
        """Assembles a GENI compliant return result for successful methods."""
        return {"geni_api": 3,
                "code": {"geni_code": 0},
                "value": result,
                "output": None}

    def _option(self, options, key, ret=False):
        return bool(options[key]) if (key in options) else ret
