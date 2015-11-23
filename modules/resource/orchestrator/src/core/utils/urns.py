from core.organisations import AllowedOrganisations
from core.utils.strings import StringUtils
from extensions.sfa.util.xrn import get_authority, urn_to_hrn


class URNUtils:
    """
    Contains common operations related to URN processing.
    """
    ## Dictionaries
    FELIX_ORGS = AllowedOrganisations.get_organisations_type()

#    @staticmethod
#    def get_authority_from_urn(urn):
#        hrn, hrn_type = urn_to_hrn(urn)
#        # Remove leaf (the component_manager part)
#        hrn_list = hrn.split(".")
#        hrn = ".".join(hrn_list[:-1])
#        authority = get_authority(hrn)
#        return authority

    @staticmethod
    def get_authority_from_urn(urn):
        authority = ""
        try:
            urn_delimiters = StringUtils.find_all(urn, "+")
            idx1 = urn_delimiters[0]
            idx2 = urn_delimiters[1]
            full_auth = urn[idx1+1:idx2]
            auth_components = full_auth.split(":")
            authority = auth_components[1]
            orgs = map(lambda x: x in authority, URNUtils.FELIX_ORGS)
            authority = URNUtils.FELIX_ORGS[orgs.index(True)]
        except:
            pass
        return authority

    @staticmethod
    # Expects URN of "authority" type, not any URN
    def get_felix_authority_from_urn(urn):
        authority = ""
        hrn, hrn_type = urn_to_hrn(urn)
        # Remove leaf (the component_manager part)
        hrn_list = hrn.split(".")
        hrn = ".".join(hrn_list[:-1])
        for hrn_element in hrn_list:
            if hrn_element in URNUtils.FELIX_ORGS:
                authority = hrn_element
                break
        # URN may not follow the standard format...
        if len(authority) == 0:
            try:
                URNUtils.get_authority_from_urn(urn)
            except:
                pass
        return authority
