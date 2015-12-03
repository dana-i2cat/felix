from core.exception import CoreException


class DelegateBaseError(CoreException):
    def __init__(self, code, name, description, comment):
        self.code = code
        self.name = name
        self.description = description
        self.comment = comment

    def __str__(self):
        return "[%s] %s (%s)" % (self.name, self.description, self.comment)


class GeneralError(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(0, 'GeneralError',
                                             "General or Unknown Error",
                                             comment)


class RPCError(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(1, 'RPCError',
                                             "Remote Procedure Call Error",
                                             comment)


class TopologyError(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(2, 'TopologyError',
                                             "Topology Error",
                                             comment)


class RSpecError(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(3, 'RSpecError',
                                             "Resource Specification Error",
                                             comment)


class AllocationError(DelegateBaseError):
    def __init__(self, comment, slice_urn, slivers, db_ids):
        super(self.__class__, self).__init__(4, 'AllocationError',
                                             "AllocationError",
                                             comment)
        self.slice_urn = slice_urn
        self.slivers = slivers
        self.db_ids = db_ids

    def details(self):
        msg = "[%s] %s (%s)" % (self.name, self.description, self.comment)
        msg += '\n\n'
        msg += "DETAILS: slice_urn=%s, slivers=%s, db_ids=%s" %\
               (self.slice_urn, self.slivers, self.db_ids)
        return msg
