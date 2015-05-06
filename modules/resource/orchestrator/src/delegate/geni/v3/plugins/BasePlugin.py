from rspecs.commons import validate
from handler.geni.v3 import exceptions as geni_ex

import core
logger = core.log.getLogger("base-plugin")


class BasePlugin(object):
    def __init__(self):
        pass

    def validate_rspec(self, rspec):
        (result, error) = validate(rspec)
        if result is not True:
            m = "RSpec validation failure: %s" % (error,)
            raise geni_ex.GENIv3GeneralError(m)
        logger.info("Validation success!")
