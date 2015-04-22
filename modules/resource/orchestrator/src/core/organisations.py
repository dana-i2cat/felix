class AllowedOrganisations:
    """
    Defines the type of allowed organisations.
    """
    ORG_I2CAT = ["i2cat"]
    ORG_PSNC = ["psnc"]
    ORG_AIST = ["aist"]
    ORG_KDDI = ["kddi"]
    ORG_IMINDS = ["iminds"]
    ORG_EICT = ["eict"]

    @staticmethod
    def get_organisations_key():
        return list(filter((lambda x: x.startswith("ORG_")), AllowedOrganisations.__dict__))

    @staticmethod
    def get_organisations_type():
        return list(AllowedOrganisations.__dict__.get(x)[0] for x in AllowedOrganisations.get_organisations_key())

    @staticmethod
    def get_organisations():
        keys = AllowedOrganisations.get_organisations_key()
        organisations = dict()
        for key in keys:
            organisations[key] = AllowedOrganisations.__dict__.get(key)[0]
        return organisations
