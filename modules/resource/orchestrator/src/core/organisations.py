class AllowedOrganisations:
    """
    Defines the type of allowed organisations.
    """
    ORG_I2CAT = ["i2cat"]
    ORG_PSNC = ["psnc"]
    ORG_AIST = ["aist", "aist2"]
    ORG_KDDI = ["kddi"]
    ORG_IMINDS = ["iminds"]
    ORG_EICT = ["eict"]

    ALIASES = {
        "psnc": ["pionier"],
        "iminds": ["iMinds"],
        "kddi": ["jgn-x.jp"],
    }

    @staticmethod
    def get_organisations_key():
        return list(filter((lambda x: x.startswith("ORG_")),
                    AllowedOrganisations.__dict__))

    @staticmethod
    def get_organisations_type():
        # Retrieve all possible organisations and flatten
        orgs = list(AllowedOrganisations.__dict__.get(x) for x in
                    AllowedOrganisations.get_organisations_key())
        return [item for sublist in orgs for item in sublist]

    @staticmethod
    def get_organisations_type_with_alias():
        # Retrieve all possible organisations and flatten
        orgs = AllowedOrganisations.get_organisations_type()
        flattened_values = [item for sublist in AllowedOrganisations.ALIASES.
                            values() for item in sublist]
        orgs.extend(flattened_values)
        return orgs

    @staticmethod
    def find_organisation_by_alias(alias):
        # If alias is not found in the proper dict, return original value
        for item in AllowedOrganisations.ALIASES.items():
            if alias in item[1]:
                return item[0]
        return alias

    @staticmethod
    def get_organisations():
        organisations = dict()
        for key in AllowedOrganisations.get_organisations_key():
            if key in organisations:
                organisations[key].extend(
                    AllowedOrganisations.__dict__.get(key))
            else:
                organisations[key] = AllowedOrganisations.__dict__.get(key)
        return organisations

    @staticmethod
    def get_organisations_with_alias():
        organisations = AllowedOrganisations.get_organisations()
        for key in AllowedOrganisations.ALIASES.keys():
            org_for_alias = AllowedOrganisations.\
                find_organisation_by_alias(key)
            value = AllowedOrganisations.ALIASES.get(key)
            # If the aliases are not already included, do so
            if org_for_alias in organisations and len(set(value).intersection(
                    set(organisations[org_for_alias]))) == 0:
                organisations[org_for_alias].extend(value)
        return organisations
