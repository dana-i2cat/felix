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
from vt_manager.communication.sfa.rspecs.elements.channel import Channel



class NITOSv1Lease:

    @staticmethod
    def add_leases(xml, leases, channels):
        
        network_elems = xml.xpath('//network')
        if len(network_elems) > 0:
            network_elem = network_elems[0]
        elif len(leases) > 0:
            network_urn = Xrn(leases[0]['component_id']).get_authority_urn().split(':')[0]
            network_elem = xml.add_element('network', name = network_urn)
        else:
            network_elem = xml
        
        # group the leases by slice and timeslots
        grouped_leases = []

        while leases:
             slice_id = leases[0]['slice_id']
             start_time = leases[0]['start_time']
             duration = leases[0]['duration']
             group = []
             
             for lease in leases:
                  if slice_id == lease['slice_id'] and start_time == lease['start_time'] and duration == lease['duration']:
                      group.append(lease)

             grouped_leases.append(group)

             for lease1 in group:
                  leases.remove(lease1)
         
        lease_elems = []       
        for lease in grouped_leases:
            #lease_fields = ['lease_id', 'component_id', 'slice_id', 'start_time', 'duration']
            lease_fields = ['slice_id', 'start_time', 'duration']
            lease_elem = network_elem.add_instance('lease', lease[0], lease_fields)
            lease_elems.append(lease_elem)

            # add nodes of this lease
            for node in lease:
                 lease_elem.add_instance('node', node, ['component_id'])

            # add reserved channels of this lease
            #channels = [{'channel_id': 1}, {'channel_id': 2}]
            for channel in channels:
                 if channel['slice_id'] == lease[0]['slice_id'] and channel['start_time'] == lease[0]['start_time'] and channel['duration'] == lease[0]['duration']:
                     lease_elem.add_instance('channel', channel, ['channel_num'])
            

    @staticmethod
    def get_leases(xml, filter={}):
        xpath = '//lease%s | //default:lease%s' % (XpathFilter.xpath(filter), XpathFilter.xpath(filter))
        lease_elems = xml.xpath(xpath)
        return NITOSv1Lease.get_lease_objs(lease_elems)

    @staticmethod
    def get_lease_objs(lease_elems):
        leases = []    
        channels = []
        for lease_elem in lease_elems:
            #get nodes
            node_elems = lease_elem.xpath('./default:node | ./node')
            for node_elem in node_elems:
                 lease = Lease(lease_elem.attrib, lease_elem)
                 lease['slice_id'] = lease_elem.attrib['slice_id']
                 lease['start_time'] = lease_elem.attrib['start_time']
                 lease['duration'] = lease_elem.attrib['duration']
                 lease['component_id'] = node_elem.attrib['component_id']
                 leases.append(lease)
            #get channels
            channel_elems = lease_elem.xpath('./default:channel | ./channel')
            for channel_elem in channel_elems:
                 channel = Channel(channel_elem.attrib, channel_elem)
                 channel['slice_id'] = lease_elem.attrib['slice_id']
                 channel['start_time'] = lease_elem.attrib['start_time']
                 channel['duration'] = lease_elem.attrib['duration']
                 channel['channel_num'] = channel_elem.attrib['channel_num']
                 channels.append(channel)

        return (leases, channels)            

