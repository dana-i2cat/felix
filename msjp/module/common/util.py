#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging.handlers

# constants
LOG_SIZE        = 5242880   #5MB
LOG_BACKUPS     = 5

def init_logger(name,logfile):
    logger = None
    try:
        logger = logging.getLogger(name)
        logHandler = logging.handlers.RotatingFileHandler(
                        filename = logfile,
                        mode = 'a', #file mode 'append'.
                        maxBytes = LOG_SIZE,
                        backupCount = LOG_BACKUPS)

        logFormat = '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s %(message)s'
        logFormatter = logging.Formatter(logFormat)
        logHandler.setFormatter(logFormatter)
        logger.addHandler(logHandler)
    except:
        print 'Failed to create logger.'
        
    return logger
