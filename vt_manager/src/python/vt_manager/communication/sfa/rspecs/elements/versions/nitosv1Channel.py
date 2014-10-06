from vt_manager.communication.sfa.util.sfalogging import logger
from vt_manager.communication.sfa.util.xml import XpathFilter
from vt_manager.communication.sfa.util.xrn import Xrn

from vt_manager.communication.sfa.rspecs.elements.element import Element
from vt_manager.communication.sfa.rspecs.elements.node import Node
from vt_manager.communication.sfa.rspecs.elements.sliver import Sliver
from vt_manager.communication.sfa.rspecs.elements.location import Location
from vt_manager.communication.sfa.rspecs.elements.hardware_type import HardwareType
from vt_manager.communication.sfa.rspecs.elements.disk_image import DiskImage
from vt_manager.communication.sfa.rspecs.elements.interface import Interface
from vt_manager.communication.sfa.rspecs.elements.bwlimit import BWlimit
from vt_manager.communication.sfa.rspecs.elements.pltag import PLTag
from vt_manager.communication.sfa.rspecs.elements.versions.nitosv1Sliver import NITOSv1Sliver
from vt_manager.communication.sfa.rspecs.elements.versions.nitosv1PLTag import NITOSv1PLTag
from vt_manager.communication.sfa.rspecs.elements.versions.pgv2Services import PGv2Services
from vt_manager.communication.sfa.rspecs.elements.lease import Lease
from vt_manager.communication.sfa.rspecs.elements.spectrum import Spectrum
from vt_manager.communication.sfa.rspecs.elements.channel import Channel


class NITOSv1Channel:

    @staticmethod
    def add_channels(xml, channels):
        
        network_elems = xml.xpath('//network')
        if len(network_elems) > 0:
            network_elem = network_elems[0]
        elif len(channels) > 0:
            # dirty hack that handles no resource manifest rspec 
            network_urn = "omf"
            network_elem = xml.add_element('network', name = network_urn)
        else:
            network_elem = xml

#        spectrum_elems = xml.xpath('//spectrum') 
#        spectrum_elem = xml.add_element('spectrum')

#        if len(spectrum_elems) > 0:
#            spectrum_elem = spectrum_elems[0]
#        elif len(channels) > 0:
#            spectrum_elem = xml.add_element('spectrum')
#        else:
#            spectrum_elem = xml

        spectrum_elem = network_elem.add_instance('spectrum', [])    
          
        channel_elems = []       
        for channel in channels:
            channel_fields = ['channel_num', 'frequency', 'standard']
            channel_elem = spectrum_elem.add_instance('channel', channel, channel_fields)
            channel_elems.append(channel_elem)


    @staticmethod
    def get_channels(xml, filter={}):
        xpath = '//channel%s | //default:channel%s' % (XpathFilter.xpath(filter), XpathFilter.xpath(filter))
        channel_elems = xml.xpath(xpath)
        return NITOSv1Channel.get_channel_objs(channel_elems)

    @staticmethod
    def get_channel_objs(channel_elems):
        channels = []    
        for channel_elem in channel_elems:
            channel = Channel(channel_elem.attrib, channel_elem)
            channel['channel_num'] = channel_elem.attrib['channel_num']
            channel['frequency'] = channel_elem.attrib['frequency']
            channel['standard'] = channel_elem.attrib['standard']

            channels.append(channel)
        return channels            

