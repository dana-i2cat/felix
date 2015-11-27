from core import dates
from core.peers import AllowedPeers
from db.db_manager import db_sync_manager
from delegate.geni.v3 import exceptions

import core
import xmlrpclib

logger = core.log.getLogger("rmadaptor")


def format_uri(protocol, user, password, address, port, endpoint):
    uri = "%s://" % str(protocol)
    if user and password:
        uri += "%s:%s@" % (str(user), str(password),)

    uri += "%s:%s" % (str(address), str(port))
    if endpoint and len(endpoint):
        if endpoint[0] == "/":
            endpoint = endpoint[1:]
        uri += "/%s" % str(endpoint)

    return uri


class AdaptorFactory(xmlrpclib.ServerProxy):
    def __init__(self, uri):
        xmlrpclib.ServerProxy.__init__(self, uri)

    @staticmethod
    def get_am_info(uri, id):
        client = SFAClient(uri)
        (type, version) = client.get_version()
        db_sync_manager.update_peer_info(id, type, version)
        return (type, version)

    @staticmethod
    def create(type, protocol, user, password, address, port, endpoint,
               id, am_type, am_version):
        uri = format_uri(protocol, user, password, address, port, endpoint)

        if am_type is None or am_version is None:
            logger.debug("We need to update the AM info for this RM...")
            (am_type, am_version) = AdaptorFactory.get_am_info(uri, id)

        logger.debug("AM type: %s, version: %s" % (am_type, am_version,))

        accepted_types = ["geni", "GENI", "geni_sfa", "GENI_SFA", "sfa", "SFA"]
        allowed_peers = AllowedPeers.get_peers()

        if am_type in accepted_types and int(am_version) <= 2:
            if type == allowed_peers.get("PEER_CRM"):
                return CRMGeniv2Adaptor(uri)
            elif type == allowed_peers.get("PEER_SDNRM"):
                return SDNRMGeniv2Adaptor(uri)
        elif am_type in accepted_types and int(am_version) == 3:
            if type == allowed_peers.get("PEER_CRM"):
                return CRMGeniv3Adaptor(uri)
            elif type == allowed_peers.get("PEER_SDNRM"):
                return SDNRMGeniv3Adaptor(uri)
            elif type == allowed_peers.get("PEER_SERM"):
                return SERMGeniv3Adaptor(uri)
            elif type == allowed_peers.get("PEER_TNRM"):
                return TNRMGeniv3Adaptor(uri)
            elif type == allowed_peers.get("PEER_RO"):
                return ROGeniv3Adaptor(uri)

        e = "Resource Manager type not implemented yet! "
        e += "Details: type=%s,version=%s" % (str(am_type), str(am_version),)
        raise exceptions.GeneralError(e)

    @staticmethod
    def create_from_db(peer_db):
        """
        Create adaptor from information in DB.
        @return adaptor_object
        @return adaptor_url (useful for domain identification)
        """
        adaptor_endpoint = peer_db.get("endpoint", "")
        if adaptor_endpoint and len(adaptor_endpoint):
            if adaptor_endpoint[0] == "/":
                adaptor_endpoint = adaptor_endpoint[1:]

        adaptor_uri = "%s://%s:%s" % (peer_db.get("protocol"),
                                      peer_db.get("address"),
                                      peer_db.get("port"))

        if adaptor_endpoint:
            adaptor_uri += "/%s" % str(adaptor_endpoint)

        adaptor = AdaptorFactory.create(
            peer_db.get("type"), peer_db.get("protocol"), peer_db.get("user"),
            peer_db.get("password"), peer_db.get("address"),
            peer_db.get("port"), peer_db.get("endpoint"), peer_db.get("_id"),
            peer_db.get("am_type"), peer_db.get("am_version"))
        return (adaptor, adaptor_uri)

    @staticmethod
    def geni_v3_credentials():
        from core.utils import calls
        try:
            (text, ucredential) = calls.getusercred(geni_api=3)
            return ucredential["geni_value"]
        except Exception as e:
            logger.error("Unable to get user-cred from CH: %s" % (e,))
            raise e


class SFAClient(AdaptorFactory):
    def __init__(self, uri, type=None, version=None):
        AdaptorFactory.__init__(self, uri)
        self.uri = uri
        self.geni_type = type
        self.geni_api_version = version

    def get_version(self):
        try:
            logger.debug("Get the required information of the peer")
            rspec_version = self.GetVersion()
            logger.debug("Rspec version: %s" % (rspec_version,))
            values = rspec_version.get("value")
            # We need at least the type and the (supported) request version
            self.geni_type = rspec_version.get("code").get("am_type")
            self.geni_api_version = values.get("geni_api")

            if not self.geni_type:  # we assume GENI as default
                self.geni_type = "geni"

            return (self.geni_type, self.geni_api_version)

        except Exception as e:
            raise exceptions.RPCError("SFA GetVersion failure: %s" % str(e))

    def __str__(self):
        return "[%s, %s, %s]" %\
            (self.uri, self.geni_type, self.geni_api_version)

    def api_version(self):
        return self.geni_api_version

    def sfa_type(self):
        return self.geni_type


class SFAv2Client(SFAClient):
    def __init__(self, uri):
        SFAClient.__init__(self, uri, type="sfa", version=2)

    def format_options(self, available):
        return {"geni_available": available,
                "geni_compress": False,
                "geni_rspec_version": {
                    "type": self.geni_type,
                    "version": self.geni_api_version, }}


class GENIv3Client(SFAClient):
    def __init__(self, uri, typee):
        SFAClient.__init__(self, uri, type="geni", version=3)
        self.typee = typee
        logger.info("GENIv3Client %s created." % (self.typee,))

    def format_options(self, available=None, compress=None, end_time=None,
                       best_effort=None, users=[]):
        options = {"geni_rspec_version": {"type": "geni",
                                          "version": 3, }}
        if available:
            options["geni_available"] = available
        if compress:
            options["geni_compress"] = compress
        if end_time:
            # Convert to rfc3339 prior to sending
            options["geni_end_time"] = dates.datetime_to_rfc3339(end_time)
        if best_effort:
            options["geni_best_effort"] = best_effort
        if users:
            options["geni_users"] = users
        return options

    def format_credentials(self, credentials):
        # Credentials must be sent in the proper format
        credentials = [{"geni_value": credentials,
                        "geni_type": "geni_sfa", }]
        return credentials

    def list_resources(self, credentials, available):
        options = self.format_options(available=available, compress=False)
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        logger.debug("%s Options: %s" % (self.typee, options,))
        try:
            params = [credentials, options, ]
            result = self.ListResources(*params)
            logger.info("\n\n\n%s ListResources result=%s\n\n\n" %
                        (self.typee, result,))
            return result

        except Exception as e:
            err = "%s ListResources failure: %s" % (self.typee, str(e))
            raise exceptions.RPCError(err)

    ## Helpers

    def __get_domain_urn_by_xmlrpcserver(self):
        """
        Prepare filter parameters to get the domain.info from the xmlrpcserver
        """
        domain_urn = ""
        try:
            #am_version = str(self.geni_api_version)
            #am_type = str(self.geni_type)
            # Look for case-independent 'am_type' and numeric 'am_type'
            #am_type_re = re.compile(am_type)
            #filter_params = {"am_version": int(am_version), "am_type": am_type_re}
            filter_params = {}
            domain_urn = db_sync_manager.get_domain_urn_from_uri(self.uri, filter_params)

        except Exception as e:
            logger.warning("get_domain_urn_from_uri failed: %s" % e)
        return domain_urn

    def __check_errors(self, result):
        domain_urn = self.__get_domain_urn_by_xmlrpcserver()
        if result.get("output") is not None:
            return False, "Error detected in the server (%s @ %s): %s" %\
                (self.typee, domain_urn, result.get("output"))
        if "geni_slivers" in result.get("value"):
            for s in result.get("value").get("geni_slivers"):
                if s.get("geni_error"):
                    return False, "Error detected in a sliver (%s @ %s): %s" %\
                        (self.typee, domain_urn, s.get("geni_error"))
        return True, ""

    def allocate(self, slice_urn, credentials, rspec, end_time):
        options = self.format_options(end_time=end_time)
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [slice_urn, credentials, rspec, options, ]
            result = self.Allocate(*params)
            logger.info("\n\n\n%s Allocate result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return (result.get("value").get("geni_rspec"),
                        result.get("value").get("geni_slivers"))

        except Exception as e:
            err = "%s Allocate failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def describe(self, urns, credentials):
        options = self.format_options()
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, options, ]
            result = self.Describe(*params)
            logger.info("\n\n\n%s Describe result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return (result.get("value").get("geni_rspec"),
                        result.get("value").get("geni_urn"),
                        result.get("value").get("geni_slivers"))

        except Exception as e:
            err = "%s Describe failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def renew(self, urns, credentials, expiration_time, best_effort):
        options = self.format_options(best_effort=best_effort)
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, expiration_time, options, ]
            result = self.Renew(*params)
            logger.info("\n\n\n%s Renew result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return result.get("value")

        except Exception as e:
            err = "%s Renew failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def status(self, urns, credentials):
        options = self.format_options()
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, options, ]
            result = self.Status(*params)
            logger.info("\n\n\n%s Status result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return (result.get("value").get("geni_urn"),
                        result.get("value").get("geni_slivers"))

        except Exception as e:
            err = "%s Status failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def perform_operational_action(self, urns, credentials, action,
                                   best_effort):
        options = self.format_options(best_effort=best_effort)
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, action, options, ]
            result = self.PerformOperationalAction(*params)
            logger.info("\n\n\n%s PerformOperationalAction result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return result.get("value")

        except Exception as e:
            err = "%s PerformOpAction failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def delete(self, urns, credentials, best_effort):
        options = self.format_options(best_effort=best_effort)
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, options, ]
            result = self.Delete(*params)
            logger.info("\n\n\n%s Delete result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return result.get("value")

        except Exception as e:
            err = "%s Delete failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)

    def provision(self, urns, credentials, best_effort, end_time, geni_users):
        options = self.format_options(best_effort=best_effort,
                                      end_time=end_time,
                                      users=geni_users)
        logger.debug("%s Options: %s" % (self.typee, options,))
        # Credentials must be sent in the proper format
        credentials = self.format_credentials(credentials)
        try:
            params = [urns, credentials, options, ]
            result = self.Provision(*params)
            logger.info("\n\n\n%s Provision result=%s\n\n\n" %
                        (self.typee, result,))

            status, err = self.__check_errors(result)
            if status is True:
                return (result.get("value").get("geni_rspec"),
                        result.get("value").get("geni_slivers"))

        except Exception as e:
            err = "%s Provision failure: %s" % (self.typee, str(e))

        raise exceptions.RPCError(err)


class CRMGeniv2Adaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)
        raise exceptions.RPCError("CRMGeniv2Adaptor not supported!")


class SDNRMGeniv2Adaptor(SFAv2Client):
    def __init__(self, uri):
        SFAv2Client.__init__(self, uri)
        raise exceptions.RPCError("SDNRMGeniv2Adaptor not supported!")


class CRMGeniv3Adaptor(GENIv3Client):
    def __init__(self, uri):
        GENIv3Client.__init__(self, uri, "CRMGeniv3")


class SDNRMGeniv3Adaptor(GENIv3Client):
    def __init__(self, uri):
        GENIv3Client.__init__(self, uri, "SDNRMGeniv3")


class SERMGeniv3Adaptor(GENIv3Client):
    def __init__(self, uri):
        GENIv3Client.__init__(self, uri, "SERMGeniv3")


class TNRMGeniv3Adaptor(GENIv3Client):
    def __init__(self, uri):
        GENIv3Client.__init__(self, uri, "TNRMGeniv3")


class ROGeniv3Adaptor(GENIv3Client):
    def __init__(self, uri):
        GENIv3Client.__init__(self, uri, "ROGeniv3")
