from resource_detector import ResourceDetector

import core
logger = core.log.getLogger("jobs")


# resource detector scheduled jobs
def sdn_resource_detector():
    try:
        rd = ResourceDetector('sdn_networking')
        rd.do_action()

    except Exception as e:
        logger.error('sdn_resource_detector failure: %s' % (e,))
