"""
This module provides logging facilities. More specifically,
it provides a way to get to a (configured) python logger.
Hence the interface of this logger is the same as the python one
(so please direct all complaints regarding this to the python people).
In order to get such a logger instance, you could insert this code
at the beginning of your module:
    import amsoil.core.log
    logger=amsoil.core.log.getLogger('SOMENAME')
whereby SOMENAME represents an optional prefix for the logging messages
(e.g. 'xplugin' would yield messages like 'd.a.te [xplugin] message')

Configuration
Please see the config.py file in the root/src-folder.

Rationale
After long discussions logging is a core service.
The main reason for having logging as a core service is that the pluginmanager
should be able to log straight away (without loading a dedicated plugin).
Also the administrator should have only one place to
edit the log config (level, file, etc.). If you had a plugin for it,
the config-plugin-service would not be available
when the pluginmanager loads.
"""

import logging
import logging.handlers
import os
from colorlog import ColoredFormatter

log_name = "resource-orchestrator"
root_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                          "../../log/"))
log_file = os.path.join(root_path, "resource-orchestrator.log")
log_level = logging.DEBUG


def getLogger(prefix=None):
    """Receive a python logger (logging.Logger) which has been
    configured by AMsoil."""
    logger = logging.getLogger(log_name)
    if prefix:
        return PrefixAdapter(logger, prefix)
    else:
        return logger


class PrefixAdapter(logging.LoggerAdapter):
    """Internal class for wrapping logging messages.
    Do not use outside this module."""
    def __init__(self, logger, prefix):
        logging.LoggerAdapter.__init__(
            self, logger, {"prefix": prefix})

    def process(self, msg, kwargs):
        prefix = self.extra["prefix"]
        return ("[%s] %s" % (prefix, msg), kwargs)

# Initialization
lhandle = logging.handlers.RotatingFileHandler(log_file, maxBytes=1000000)
lhandle.setLevel(log_level)
colormap = {'DEBUG': 'green', 'INFO': 'yellow', 'WARNING': 'blue',
            'ERROR': 'red', 'CRITICAL': 'purple'}
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] - %(message)s",
    datefmt=None, reset=True, log_colors=colormap,
    secondary_log_colors={}, style='%')
lhandle.setFormatter(formatter)
logger = getLogger()
logger.addHandler(lhandle)
logger.setLevel(log_level)
logger.info("Logging initialized")
