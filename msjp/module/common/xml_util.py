#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def to_array(item):
    # variable &  dictionary
    if isinstance(item, list) != True:
        items = []
        items.append(item)
        return items
    else:
        return item
