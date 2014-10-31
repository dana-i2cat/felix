from delegate.geni.v3.rspecs.tnrm.request_formatter import DEFAULT_XS,\
    TNRMv3RequestFormatter, DEFAULT_XMLNS, DEFAULT_SHARED_VLAN,\
    DEFAULT_REQ_SCHEMA_LOCATION


class SERMv3RequestFormatter(TNRMv3RequestFormatter):
    def __init__(self, xmlns=DEFAULT_XMLNS, xs=DEFAULT_XS,
                 sharedvlan=DEFAULT_SHARED_VLAN,
                 schema_location=DEFAULT_REQ_SCHEMA_LOCATION):
        super(SERMv3RequestFormatter, self).__init__(
            xmlns, xs, sharedvlan, schema_location)
