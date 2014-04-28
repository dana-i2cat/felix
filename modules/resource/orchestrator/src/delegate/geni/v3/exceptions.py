from core.exception import CoreException


class DelegateBaseError(CoreException):
    def __init__(self, code, name, description, comment):
        self.code = code
        self.name = name
        self.description = description
        self.comment = comment

    def __str__(self):
        return "[%s] %s (%s)" % (self.name, self.description, self.comment)


class DHCPLeaseNotFound(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(1, 'DHCPLeaseNotFound',
                                             "Lease Not Found", comment)


class DHCPMaxLeaseDurationExceeded(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(2, 'DHCPMaxLeaseDurationExceeded',
                                             "Max Lease Duration Exceeded",
                                             comment)


class DHCPLeaseAlreadyTaken(DelegateBaseError):
    def __init__(self, comment):
        super(self.__class__, self).__init__(3, 'DHCPLeaseAlreadyTaken',
                                             "Lease Already Taken". comment)
