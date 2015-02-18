#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging.handlers
from xml.etree import ElementTree
from xml.dom import minidom

# constants
LOG_SIZE        = 5242880   # 5MB
LOG_BACKUPS     = 5

def get_config_param(confInfo,section,item):
    if confInfo.has_section(section):
        ret = confInfo.get(section, item)
    else:
        ret = confInfo.get('DEFAULT', item)

    if ret is None or ret == '':
        return ret

    # trailing "/" is delete.
    ret = ret.rstrip("/")

    # to tuple or list
    if '(' == ret[0] or '[' == ret[0]:
        ret = eval(ret)
    return ret

def getint_config_param(confInfo,section,item):
    if confInfo.has_section(section):
        ret = confInfo.getint(section, item)
    else:
        ret = confInfo.getint('DEFAULT', item)
    return ret

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def to_array(item):
    if not(isinstance(item, list) or isinstance(item, tuple)):
        items = list()
        items.append(item)
        return items
    else:
        return item

def to_listinlist(item):
    item = to_array(item)
    if not(isinstance(item[0], list) or isinstance(item[0], tuple)):
        items = list()
        items.append(item)
        return items
    else:
        return item

def isinteger(x):
    if x == int(x):
        return int(x)
    else:
        return x

def init_logger(name,logfile):
    logger = None
    try:
        logger = logging.getLogger(name)
        logHandler = logging.handlers.RotatingFileHandler(
                        filename = logfile,
                        mode = 'a', # file mode 'append'.
                        maxBytes = LOG_SIZE,
                        backupCount = LOG_BACKUPS)

        logFormat = '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s %(message)s'
        logFormatter = logging.Formatter(logFormat)
        logHandler.setFormatter(logFormatter)
        logger.addHandler(logHandler)
    except:
        print 'Failed to create logger.'
        
    return logger
