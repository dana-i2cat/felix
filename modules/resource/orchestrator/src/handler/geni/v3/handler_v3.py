import ast
import base64
import inspect
import traceback
import zlib

from handler.geni.v3 import exceptions as geni_ex

from core.config import ConfParser
from core import dates
from core import log
logger = log.getLogger("handlergeniv3")

from credentials.gcfmanager import GCFCredentialManager
from server.flask.flaskserver import FlaskServer
# Create and register the RPC server
flaskserver = FlaskServer()
from server.flask.flaskxmlrpc import FlaskXMLRPC
xmlrpc = FlaskXMLRPC(flaskserver)


class GENIv3Handler(xmlrpc.Dispatcher):

    def __init__(self):
        super(GENIv3Handler, self).__init__(logger)
        self._delegate = None
        self._verify_users =\
            ast.literal_eval(ConfParser("geniv3.conf").get("certificates").
                             get("verify_users"))
        self.__credential_manager = GCFCredentialManager()

    def setDelegate(self, geniv3delegate):
        self._delegate = geniv3delegate

    def getDelegate(self):
        return self._delegate

    # RSPEC3_NAMESPACE= "http://www.geni.net/resources/rspec/3"

    def GetVersion(self):
        """Returns the version of this interface.
        This method can be hard coded, since we are actually setting up the
        GENI v3 API, only. For the RSpec extensions, we ask the delegate."""
        # No authentication necessary

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
             "extensions": request_extensions,
            },
        ]
        ad_rspec_versions = [
            {"type": "geni", "version": 3,
             "schema": "http://www.geni.net/resources/rspec/3/ad.xsd",
             "namespace": "http://www.geni.net/resources/rspec/3",
             "extensions": ad_extensions,
            },
        ]
        credential_types = [ {"geni_type": "geni_sfa", "geni_version": 3} ]

        return self._successReturn(
            {"geni_api": 3,
             "geni_api_versions": {"3": "/xmlrpc/geni/3/"},  # absolute URL
             "geni_request_rspec_versions": request_rspec_versions,
             "geni_ad_rspec_versions": ad_rspec_versions,
             "geni_credential_types": credential_types,
             "geni_single_allocation": is_single_allocation,
             "geni_allocate": allocation_mode,
            })

    def ListResources(self, credentials, options):
        """Delegates the call and unwraps the needed parameter.
        Also takes care of the compression option."""
        self.__validate_credentials(credentials)

        logger.debug("ListResources options=%s" % (options,))
        # Interpret options
        geni_available = self._option(options, "geni_available")

        # check version and delegate
        try:
            self._checkRSpecVersion(options["geni_rspec_version"])
            result = self._delegate.list_resources(self.requestCertificate(),
                                                   credentials, geni_available)
        except Exception as e:
            return self._errorReturn(e)

        # Interpret geni_compress option and return compressed (if requested)
        result = self._interpret_geni_compress(result, options)

        return self._successReturn(result)

    def Describe(self, urns, credentials, options):
        """Delegates the call and unwraps the needed parameter.
        Also takes care of the compression option."""
        self.__validate_credentials(credentials)

        logger.debug("Describe urns=%s, options=%s" % (urns, options,))

        try:
            self._checkRSpecVersion(options["geni_rspec_version"])
            result = self._delegate.describe(urns, self.requestCertificate(),
                                             credentials)
            # change datetimes to strings
            result["geni_slivers"] =\
                self._convertExpiresDate(result["geni_slivers"])

        except Exception as e:
            return self._errorReturn(e)

        # Interpret geni_compress option and return compressed (if requested)
        result = self._interpret_geni_compress(result, options)

        return self._successReturn(result)

    def Allocate(self, slice_urn, credentials, rspec, options):
        """Delegates the call and unwraps the needed parameter.
        Also converts the incoming timestamp to python and the outgoing
        to geni compliant date format."""
        self.__validate_credentials(credentials)

        logger.debug("Allocate urn=%s, options=%s" % (slice_urn, options,))
        geni_end_time = None
        if "geni_end_time" in options:
            geni_end_time = dates.rfc3339_to_datetime(options["geni_end_time"])

        # TODO check the end_time against the duration of the credential
        try:
            # delegate
            # omni does not send this option
            # self._checkRSpecVersion(options["geni_rspec_version"])
            r_rspec, r_sliver_list = self._delegate.allocate(
                slice_urn, self.requestCertificate(),
                credentials, rspec, geni_end_time)

            # change datetimes to strings
            result = {"geni_rspec": r_rspec,
                      "geni_slivers": self._convertExpiresDate(r_sliver_list)}

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Renew(self, urns, credentials, expiration_time_str, options):
        self.__validate_credentials(credentials)

        logger.debug("Renew urns=%s, options=%s" % (urns, options,))
        geni_best_effort = self._option(options, "geni_best_effort")
        expiration_time = dates.rfc3339_to_datetime(expiration_time_str)
        try:
            # delegate
            result = self._delegate.renew(urns, self.requestCertificate(),
                                          credentials, expiration_time,
                                          geni_best_effort)
            # change datetimes to strings
            result = self._convertExpiresDate(result)

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def Provision(self, urns, credentials, options):
        self.__validate_credentials(credentials)

        logger.debug("Provision urns=%s, options=%s" % (urns, options,))
        geni_best_effort = self._option(options, "geni_best_effort")
        geni_users = options.get("geni_users", [])
        geni_end_time = None
        if "geni_end_time" in options:
            geni_end_time = dates.rfc3339_to_datetime(options["geni_end_time"])

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
        self.__validate_credentials(credentials)

        logger.debug("Status urns=%s, options=%s" % (urns, options,))
        try:
            r_sliceurn, r_sliver_list = self._delegate.status(
                urns, self.requestCertificate(), credentials)

            result = {"geni_urn": r_sliceurn,
                      "geni_slivers": self._convertExpiresDate(r_sliver_list)}

        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    def PerformOperationalAction(self, urns, credentials, action, options):
        self.__validate_credentials(credentials)

        logger.debug("PerformOperationalAction urns=%s, options=%s" %
                     (urns, options,))
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
        self.__validate_credentials(credentials)

        logger.debug("Delete urns=%s, options=%s" % (urns, options,))
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
        self.__validate_credentials(credentials)

        logger.debug("Shutdown urn=%s, options=%s" % (slice_urn, options,))
        try:
            result = bool(self._delegate.shutdown(slice_urn,
                                                  self.requestCertificate(),
                                                  credentials))
        except Exception as e:
            return self._errorReturn(e)

        return self._successReturn(result)

    # ---- helper methods

    def __validate_credentials(self, credentials):
        if self._verify_users:
            try:
                # Obtain the name of the method calling this one
                method_name = inspect.stack()[1][3]
                # Permissiosn for the calling method will be properly verified against creds
                self.__credential_manager.validate_for(method_name, credentials)
            except Exception as e:
                raise geni_ex.GENIv3GeneralError(str(e))

    def _interpret_geni_compress(self, result, options):
        # Read options to look for the value of geni_compress
        geni_compress = self._option(options, "geni_compressed") 
        # Compress result if client requests it
        if geni_compress:
            result = base64.b64encode(zlib.compress(str(result)))
        return result

    def _convertExpiresDate(self, sliver_list):
        """
        Converts datetime objects received from the delegate into strings.
        This is the expected returned type for the 'geni_expires' value.
        """
        for slhash in sliver_list:
            if slhash["geni_expires"] is None:
                continue

            if not dates.is_date_or_rfc3339(slhash["geni_expires"]):
                raise ValueError("Given geni_expires in sliver_list hash " +
                                 "retrieved from delegate's method is not " +
                                 "a python datetime object.")
            # If date received is "datetime.datetime", convert to rfc3339
            if dates.is_date(slhash["geni_expires"]):
                slhash["geni_expires"] =\
                    dates.datetime_to_rfc3339(slhash["geni_expires"])
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
                "code": {"geni_code": e.code},
                "output": str(e)}

    def _successReturn(self, result):
        """Assembles a GENI compliant return result for successful methods."""
        return {"geni_api": 3,
                "code": {"geni_code": 0},
                "value": result,
                }

    def _option(self, options, key, ret=False):
        return bool(options[key]) if (key in options) else ret
