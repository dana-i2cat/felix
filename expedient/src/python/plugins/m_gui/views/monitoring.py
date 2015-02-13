'''
Created on Dec 17, 2014

@author: j.fujimoto
'''
import xmltodict, urllib, urllib2
from datetime import datetime
import pytz
import calendar
import logging
logger = logging.getLogger("logging for m_gui")

# django
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, get_callable
from django.views.generic import list_detail, simple
from django.conf import settings

# expedient
from expedient.common.utils.plugins.pluginloader import PluginLoader as PLUGINLOADER

# mgui
from m_gui.forms.monitoring import MonitorSDNForm, MonitorCPForm

class MSRestClient(object):

    def __init__(self):
        uri = PLUGINLOADER.plugin_settings.get("m_gui").get("mgui").get("ms_rest_uri")
        logger.info("MS_REST_URI=%s" % uri)
        self._endpoint = uri
        self._format = "xml"

    @staticmethod
    def encode_utf8(str):
        # encode the unicode to utf-8
        return str.encode('utf-8')

    @staticmethod
    def to_array(item, key):
        items = []
        # item is not dictionary
        if isinstance(item, dict) != True:
            return items

        # key is not exist
        if item.has_key(key) == False:
            return items

        # variables and dictionary convert to array
        if isinstance(item[key], list) != True:
            items.append(item[key])
            return items
        else:
            return item[key]

    @staticmethod
    def localtime_to_utc(datestr, tz):
#        logger.debug("datestr:%s" % (datestr))

        # datetime string to datetime(aware)
        datetime_aware = datetime.strptime(datestr, '%Y/%m/%d %H:%M').replace(tzinfo=pytz.timezone(tz))
#        logger.debug("to datetime_aware:%s" % (datetime_aware))

        # datetime(aware) to datetime(UTC)
        utctime = datetime_aware.astimezone(pytz.utc)
#        logger.debug("to utctime:%s" % (utctime))

        # datetime(UTC) to utc(UNIX time)
        utc = calendar.timegm(utctime.timetuple())
#        logger.debug("to UNIX TIME:%s" % (utc))
        return utc

    @staticmethod
    def utc_to_localtime(utc, tz):
#        logger.debug("utc:%s" % (utc))

        # utc(UNIX time) to datetime(UTC)
        datetime_utc = datetime.fromtimestamp(float(utc), pytz.utc)
#        logger.debug("datetime_utc:%s" % (datetime_utc))

        # datetime(UTC) to datetime(localtime)
        localtime = datetime_utc.astimezone(pytz.timezone(tz)).strftime("%Y/%m/%d %H:%M:%S")
#        logger.debug("localtime:%s" % (localtime))
        return localtime

    @staticmethod
    def image_url(type):
        image_url = ""
        try:
            if type == "switch":
                image_url = reverse('img_media_openflow', args=("switch-tiny.png",))
            elif type == "server":
                image_url = reverse('img_media_vt_plugin', args=("server-tiny.png",))
            elif type == "vm":
                image_url = reverse('img_media_vt_plugin', args=("server-tiny.png",))
        except:
            image_url = 'host-tiny.png'
        return image_url

    @staticmethod
    def owner_to_name(id):
        name = ""
        # ex. owner is urn:publicid:IDN+geni:gpo:gcf+user+user1
        # split on +user+
        idlist = id.split('+user+')
        # next item of +user+
        name = idlist[len(idlist)-1]
        return name

    @staticmethod
    def nodeid_to_name(id, type):
        name = ""
        if type == "switch":
            # ex. switch's nodeid is urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01
            # split on +datapath+
            idlist = id.split('+datapath+')
            # next item of +datapath+
            name = idlist[len(idlist)-1]
        elif type == "server":
            # ex. server's nodeid is urn:publicid:IDN+ocf:jgnx:vtam:server1.rise.jgnx.net
            # split on :vtam:
            idlist = id.split(':vtam:')
            # next item of :vtam:
            name = idlist[len(idlist)-1]
        elif type == "vm":
            # ex. vm's nodeid is urn:publicid:IDN+ocf:jgnx:vtam:server1.rise.jgnx.net+sliver+edge-node-2
            # split on +sliver+
            idlist = id.split('+sliver+')
            # next item of +sliver+
            name = idlist[len(idlist)-1]
        return name

    @staticmethod
    def nwname_to_name(id, type):
        name = ""
        if type == "physical":
            # ex. physical's networkname is urn:publicid:IDN+ocf:jgnx
            # split on +ocf:
            idlist = id.split('+ocf:')
            # next item of +ocf:
            name = idlist[len(idlist)-1]
        elif type == "slice":
            # ex. slice's networkname is urn:publicid:IDN+ocf:i2cat+slice+slice1
            # split on +slice+
            idlist = id.split('+slice+')
            # next item of +slice+
            name = idlist[len(idlist)-1]
        return name

    @staticmethod
    def ifid_to_name(id, type):
        name = ""
        if type == "switch":
            # ex. switch's interfaceid is urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:04_5
            # split on +datapath+
            idlist = id.split('+datapath+')
            # ex. split's id is 00:10:00:00:00:00:00:04_5
            # re-split on _
            idlist = idlist[len(idlist)-1].split('_')
            # next item of _
            name = idlist[len(idlist)-1]
        elif type == "server" or type == "vm":
            # ex. servers's interfaceid is urn:publicid:IDN+ocf:jgnx:vtam:server1.rise.jgnx.net+interface+eth1
            # ex. vm's interfaceid is urn:publicid:IDN+ocf:i2cat:vtam:edge-node-1+interface+if1
            # split on +interface+
            idlist = id.split('+interface+')
            # next item of +interface+
            name = idlist[len(idlist)-1]
        return name

    def get_slice_list(self, user):
        logger.debug("get_slice_list user=%s" % user)

        # get topology
        request_url = "%s%s" % (self._endpoint, "topology/")
        logger.debug("request_url=%s" % (request_url))
        slices = []
        try:
            # call API
            response = urllib2.urlopen(request_url).read()

            # parse response(XML)
            topologys_xml = xmltodict.parse(response)

            slice_no = 0
            for topology in MSRestClient.to_array(topologys_xml['topology_list'], 'topology'):
                # ignore physical topology
                if topology['@type'] == 'physical':
                    continue
                # filter by user
                user_work = MSRestClient.owner_to_name(topology['@owner'])
                if user.is_superuser:
                    user_work = str(user)
                if user_work != str(user):
                    continue
                # get information
                slice_no += 1
                slice_data = dict()
                slice_data['no'] = str(slice_no)
                slice_data['id'] = MSRestClient.encode_utf8(topology['@name'])
                slice_data['name'] = MSRestClient.nwname_to_name(topology['@name'], topology['@type'])
                # TODO:description
                slice_data['description'] = ""
                slice_data['owner'] = MSRestClient.owner_to_name(topology['@owner'])
#                slice_data['uri'] = MSRestClient.encode_utf8(topology['uri'])
                logger.debug("slice data=%s" % str(slice_data))
                slices.append(slice_data)

        except Exception as e:
            print "Exception %s" % str(e)
            logger.error("Exception %s" % str(e))

        return slices

    def get_topology_list(self, user, slice_id):
        logger.debug("get_slice user=%s, slice_id=%s" % (user, slice_id))

        # get topology
        request_url = "%s%s" % (self._endpoint, "topology/")
        logger.debug("request_url=%s" % (request_url))
        slice = None
        physicals = []
        try:
            # call API
            response = urllib2.urlopen(request_url).read()

            # parse response(XML)
            topologys_xml = xmltodict.parse(response)

            slice_no = 0
            for topology in MSRestClient.to_array(topologys_xml['topology_list'], 'topology'):
                if topology['@type'] == 'physical':
                    physical_data = dict()
                    physical_data['id'] = MSRestClient.encode_utf8(topology['@name'])
                    physical_data['name'] = MSRestClient.nwname_to_name(topology['@name'], topology['@type'])
                    # TODO:description
                    physical_data['description'] = ""
#                    physical_data['uri'] = MSRestClient.encode_utf8(topology['uri'])
                    logger.debug("physical data=%s" % str(physical_data))
                    physicals.append(physical_data)
                elif topology['@type'] == 'slice':
                    # filter by user
                    user_work = MSRestClient.owner_to_name(topology['@owner'])
                    if user.is_superuser:
                        user_work = str(user)
                    if user_work != str(user):
                        continue
                    slice_no += 1
                    if topology['@name'] == slice_id:
                        slice_data = dict()
                        slice_data['no'] = str(slice_no)
                        slice_data['id'] = MSRestClient.encode_utf8(topology['@name'])
                        slice_data['name'] = MSRestClient.nwname_to_name(topology['@name'], topology['@type'])
                        # TODO:description
                        slice_data['description'] = ""
                        slice_data['owner'] = MSRestClient.owner_to_name(topology['@owner'])
#                        slice_data['uri'] = MSRestClient.encode_utf8(topology['uri'])
                        logger.debug("slice data=%s" % str(slice_data))
                        slice = slice_data
        except Exception as e:
            print "Exception %s" % str(e)
            logger.error("Exception %s" % str(e))

        topology = {'slice': slice, 'physicals': physicals}
        return topology

    def get_slice_detail(self, user, topology):
        logger.debug("get_slice_detail user=%s, topology=%s" % (user, topology))

        detail = dict()
        try:
            # get topology data
            detail['slice'] = self.get_topology('topology/slice/' + topology['slice']['id'], 'slice')
            detail['physical'] = self.get_topology('topology/physical', 'physical', topology['physicals'])
            detail['n_islands'] = len(topology['physicals'])

            # node status setting
            self.set_last_monitoring_status(detail, 'slice', 'sdn', topology['slice']['id'])
            self.set_last_monitoring_status(detail, 'slice', 'cp', topology['slice']['id'])
            self.set_last_monitoring_status(detail, 'physical', 'sdn')
            self.set_last_monitoring_status(detail, 'physical', 'cp')

            # connection info setting
            self.set_connection_info(detail, 'slice')
            self.set_connection_info(detail, 'physical')

            # relation info setting
            self.set_relation_info(detail)

        except Exception as e:
            print "Exception %s" % str(e)
            logger.error("Exception %s" % str(e))

        return detail

    def get_monitoring_data(self, param):
        logger.debug("get_monitoring_data param=%s" % (str(param)))

        mds = []
        try:
            settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
            if param['monitor'] == 'sdn':
                status = MonitoringUtility.get_metric_setting(settings, 'monitoring_sdn_metric', 'Status')
            elif param['monitor'] == 'cp':
                status = MonitoringUtility.get_metric_setting(settings, 'monitoring_cp_metric', 'Status')
            status_1st_value = MonitoringUtility.get_1st_value(status)

            # make parameters
            url_param = {}
            url_param['type'] = param['metric'][4]
            url_param['topology'] = param['node_location']
            url_param['node'] = param['node_id']
            if param['monitor'] == 'sdn':
                url_param['port'] = param['node_port']
            url_param['time-start'] = MSRestClient.localtime_to_utc(param['datefrom'], param['timezone'])
            url_param['time-end'] = MSRestClient.localtime_to_utc(param['dateto'], param['timezone'])
            url_param['limit'] = param['limit']
            if param['monitor'] == 'sdn':
                monitor_url = 'network_sdn/'
            elif param['monitor'] == 'cp':
                monitor_url = 'cp/'
            request_url = "%smonitoring/%s%s/" % (self._endpoint, monitor_url, param['network'])
            url_param_encode = urllib.urlencode(url_param, doseq=True)
            request_url += "?" + url_param_encode
            logger.info("request_url=%s" % (request_url))

            # call API
            response = urllib2.urlopen(request_url).read()

            # parse response(XML)
            md_xml = xmltodict.parse(response)

            # monitoring data getting
            for topology in MSRestClient.to_array(md_xml['monitoring-data']['topology_list'], 'topology'):
                for node in MSRestClient.to_array(topology, 'node'):
                    if param['monitor'] == 'sdn':
                        for port in MSRestClient.to_array(node, 'port'):
                            for parameter in MSRestClient.to_array(port, 'parameter'):
                                for value in MSRestClient.to_array(parameter, 'value'):
                                    md = self.search_monitoring_data(mds, value['@timestamp'])
                                    if param['metric'][2] == 1:
                                        strvalue = value['#text']
                                    elif param['metric'][2] == 2:
                                        strvalue = MonitoringUtility.get_value(status, value['#text'])
                                    md[parameter['@type']] = strvalue
                    elif param['monitor'] == 'cp':
                        for parameter in MSRestClient.to_array(node, 'parameter'):
                            for value in MSRestClient.to_array(parameter, 'value'):
                                md = self.search_monitoring_data(mds, value['@timestamp'])
                                if param['metric'][2] == 1:
                                    strvalue = value['#text']
                                elif param['metric'][2] == 2:
                                    strvalue = MonitoringUtility.get_value(status, value['#text'])
                                md[parameter['@type']] = strvalue

            # convert UNIX TIME(UTC) to localtime(str)
            for md in mds:
                md['datetime'] = MSRestClient.utc_to_localtime(md['datetime'], param['timezone'])


        except Exception as e:
            print "Exception %s" % str(e)
            logger.error("Exception %s" % str(e))

#        logger.debug("mds=%s" % str(mds))
        return mds

    def interface_to_nodeno(self, detail, search, id):
#        logger.debug("search=%s, id=%s" % (str(detail[search]['nodes']), id))

        # interfaces searching
        for node in detail[search]['nodes']:
            for interface in node['interfaces']:
                if id == interface['id']:
                    return node['no'], node, interface

        return

    def node_to_nodeno(self, detail, search, id):
#        logger.debug("search=%s, id=%s" % (str(detail[search]['nodes']), id))

        # nodes searching
        for node in detail[search]['nodes']:
            if id == node['id']:
                return node['no'], node

        return

    def set_last_monitoring_status(self, detail, network, monitor, id=None):
#        logger.debug("set_last_monitoring_status")

        try:
            settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
            if monitor == 'sdn':
                status = MonitoringUtility.get_metric_setting(settings, 'monitoring_sdn_metric', 'Status')
            elif monitor == 'cp':
                status = MonitoringUtility.get_metric_setting(settings, 'monitoring_cp_metric', 'Status')
            status_1st_value = MonitoringUtility.get_1st_value(status)

            # make parameters
            url_param = {}
            url_param['type'] = "status"
            if network == 'slice':
                url_param['topology'] = id
            url_param['time-start'] = 0
            url_param['time-end'] = calendar.timegm(datetime.utcnow().timetuple())
            url_param['limit'] = 1
            if monitor == 'sdn':
                monitor_url = 'network_sdn/'
            elif monitor == 'cp':
                monitor_url = 'cp/'
            request_url = "%smonitoring/%s%s/" % (self._endpoint, monitor_url, network)
            url_param_encode = urllib.urlencode(url_param)
            request_url += "?" + url_param_encode
            logger.debug("request_url=%s" % (request_url))

            # call API
            response = urllib2.urlopen(request_url).read()

            # parse response(XML)
            md_xml = xmltodict.parse(response)

            # monitoring data(status) getting
            for topology in MSRestClient.to_array(md_xml['monitoring-data']['topology_list'], 'topology'):
                for node in MSRestClient.to_array(topology, 'node'):
                    if monitor == 'sdn':
                        for port in MSRestClient.to_array(node, 'port'):
                            for parameter in MSRestClient.to_array(port, 'parameter'):
                                for value in MSRestClient.to_array(parameter, 'value'):
                                    strvalue = MonitoringUtility.get_value(status, value['#text'])
                                    if strvalue != status_1st_value:
                                        logger.debug("node=%s, value=%s(%s)" % (node, value['#text'], strvalue))
                                        targetno, target = self.node_to_nodeno(detail, network, node['@id'])
                                        target["status"] = strvalue
                                        for interface in target['interfaces']:
                                            if interface['port'] == port['@num']:
                                                interface['status'] = strvalue
                                                break
                    elif monitor == 'cp':
                        for parameter in MSRestClient.to_array(node, 'parameter'):
                            for value in MSRestClient.to_array(parameter, 'value'):
                                strvalue = MonitoringUtility.get_value(status, value['#text'])
                                if strvalue != status_1st_value:
                                    logger.debug("node=%s, value=%s(%s)" % (node, value['#text'], strvalue))
                                    targetno, target = self.node_to_nodeno(detail, network, node['@id'])
                                    target["status"] = strvalue


        except Exception as e:
            print "Exception %s" % str(e)
            logger.error("Exception %s" % str(e))

        return

    def set_connection_info(self, detail, network):

        settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
        sdn_status = MonitoringUtility.get_metric_setting(settings, 'monitoring_sdn_metric', 'Status')
        cp_status = MonitoringUtility.get_metric_setting(settings, 'monitoring_cp_metric', 'Status')
        sdn_1st_value = MonitoringUtility.get_1st_value(sdn_status)
        cp_1st_value = MonitoringUtility.get_1st_value(cp_status)
        link_2nd_value = MonitoringUtility.get_2nd_value(sdn_status)

        # link scanning
        for link in detail[network]['links']:
#            logger.debug("%s %s" % (link['source']['id'], link['target']['id']))
            # convert id to no
            link['source']['no'], node_source, interface_source = self.interface_to_nodeno(detail, network, link['source']['id'])
            link['target']['no'], node_target, interface_target = self.interface_to_nodeno(detail, network, link['target']['id'])

            # connection info setting
            connection_data = dict()
            connection_data['id'] = interface_source['id']
            connection_data['name'] = MSRestClient.ifid_to_name(interface_source['id'], node_source['type'])
            connection_data['port'] = interface_source['port']
            connection_data['dest'] = node_target['name']
            connection_data['destkind'] = node_target['type']
            connection_data['destport'] = interface_target['port']
#            logger.debug("connection data=%s" % str(connection_data))
            node_source['connections'].append(connection_data)
            connection_data = dict()
            connection_data['id'] = interface_target['id']
            connection_data['name'] = MSRestClient.ifid_to_name(interface_target['id'], node_target['type'])
            connection_data['port'] = interface_target['port']
            connection_data['dest'] = node_source['name']
            connection_data['destkind'] = node_source['type']
            connection_data['destport'] = interface_source['port']
#            logger.debug("connection data=%s" % str(connection_data))
            node_target['connections'].append(connection_data)

            # link status setting
            if node_source['type'] == "switch":
                if interface_source['status'] != sdn_1st_value:
                    link['status'] = link_2nd_value
            else:
                if node_source['status'] != cp_1st_value:
                    link['status'] = link_2nd_value

            if node_target['type'] == "switch":
                if interface_target['status'] != sdn_1st_value:
                    link['status'] = link_2nd_value
            else:
                if node_target['status'] != cp_1st_value:
                    link['status'] = link_2nd_value

        return

    def set_relation_info(self, detail):

        # relationsip slice topology and physical topology
        detail['slice']['relations'] = []
        for node in detail['slice']['nodes']:
            # generate relation data
            relation_data = dict()
            # convert id to no
            relation_data['slice'], slice_node = self.node_to_nodeno(detail, 'slice', node['id'])
            # physical topology searching
            relation_count = 0
            if node['type'] == "switch":
                relation_data['physical'], physical_node = self.node_to_nodeno(detail, 'physical', node['id'])
                relation_count = detail['slice']['relation_nodes'].count(node['id'])
            elif node['type'] == "vm":
                relation_data['physical'], physical_node = self.node_to_nodeno(detail, 'physical', node['server'])
                relation_count = detail['slice']['relation_nodes'].count(node['server'])
                physical_node['vms'].append(node['name'])
            # TODO:value
            relation_data['value'] = ""
#            logger.debug("relation data=%s" % str(relation_data))
            detail['slice']['relations'].append(relation_data)

            # relation information for node
            node['relation'] = relation_data['physical']
            if relation_count > 1:
                physical_node['relation_branch'] += 1
                node['relation_branch'] = physical_node['relation_branch']

        return

    def get_islandno(self, islands, network_name):
#        logger.debug("get_islandno islands=%s, network_name=%s" % (str(islands), network_name))

        # slice's group_no is only 0
        group_no = 0
        if islands != None:
            for island in islands:
                group_no += 1
                if island['id'] == network_name:
                    break

        return group_no

    def get_topology(self, uri, network, islands=None):
        logger.debug("get_topology uri=%s" % (uri))
        request_url = "%s%s" % (self._endpoint, uri)

        topology_data = dict()
        topology_data['relation_nodes'] = []
        topology_data['nodes'] = []
        topology_data['links'] = []
        node_no = 0

        settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
        sdn_status = MonitoringUtility.get_metric_setting(settings, 'monitoring_sdn_metric', 'Status')
        cp_status = MonitoringUtility.get_metric_setting(settings, 'monitoring_cp_metric', 'Status')

        # call API
        response = urllib2.urlopen(request_url).read()

        # parse response(XML)
        topologys_xml = xmltodict.parse(response)

        # topology loop
        for topology in MSRestClient.to_array(topologys_xml['topology_list'], 'topology'):

            # node information setting
            for node in MSRestClient.to_array(topology, 'node'):
                node_data = dict()
                node_data['no'] = str(node_no)
                node_data['id'] = MSRestClient.encode_utf8(node['@id'])
                node_data['name'] = MSRestClient.nodeid_to_name(node['@id'], node['@type'])
                node_data['type'] = MSRestClient.encode_utf8(node['@type'])
                node_data['location'] = MSRestClient.encode_utf8(topology['@name'])
                node_data['location_name'] = MSRestClient.nwname_to_name(topology['@name'], network)
                # TODO:description
                node_data['description'] = "" 
                node_data['image_url'] = MSRestClient.image_url(node_data['type'])
                node_data['group'] = str(self.get_islandno(islands, node_data['location']))
                node_data['interfaces'] = []
                for interface in MSRestClient.to_array(node, 'interface'):
                    interface_data = dict()
                    interface_data['id'] = MSRestClient.encode_utf8(interface['@id'])
                    interface_data['name'] = MSRestClient.ifid_to_name(interface['@id'], node_data['type'])
                    interface_data['port'] = 0
                    if node_data['type'] == "switch":
                        interface_data['status'] = MonitoringUtility.get_1st_value(sdn_status)
                        interface_data['port'] = MSRestClient.encode_utf8(interface['port']['@num'])
                    node_data['interfaces'].append(interface_data)
                node_data['connections'] = []
                # for each node types
                if node_data['type'] == "switch":
                    topology_data['relation_nodes'].append(node_data['id'])
                    node_data['status'] = MonitoringUtility.get_1st_value(sdn_status)
                elif node_data['type'] == "vm":
                    node_data['server'] = MSRestClient.encode_utf8(node['vm_info']['server_id'])
                    topology_data['relation_nodes'].append(node_data['server'])
                    node_data['status'] = MonitoringUtility.get_1st_value(cp_status)
                elif node_data['type'] == "server":
                    node_data['vms'] = []
                    node_data['status'] = MonitoringUtility.get_1st_value(cp_status)
                node_data['relation'] = None
                node_data['relation_branch'] = 0
                logger.debug("node data=%s" % str(node_data))
                topology_data['nodes'].append(node_data)
                node_no += 1

            # link information setting
            for link in MSRestClient.to_array(topology, 'link'):
                # source info
                source_data = dict()
                source_data['location'] = MSRestClient.encode_utf8(topology['@name'])
                source_data['id'] = MSRestClient.encode_utf8(link['interface_ref'][0]['@client_id'])
                # target info
                target_data = dict()
                target_data['location'] = MSRestClient.encode_utf8(topology['@name'])
                target_data['id'] = MSRestClient.encode_utf8(link['interface_ref'][1]['@client_id'])
                link_data = dict()
                link_data['type'] = MSRestClient.encode_utf8(link['@type'])
                link_data['source'] = source_data
                link_data['target'] = target_data
                link_data['status'] = MonitoringUtility.get_1st_value(sdn_status)
                # TODO:value
                link_data['value'] = ""
                logger.debug("link data=%s" % str(link_data))
                topology_data['links'].append(link_data)

        return topology_data

    def search_monitoring_data(self, mds, dt):
#        logger.debug("mds=%s, dt=%s" % (str(mds), str(dt)))

        # monitoring data searching(key is datetime)
        for md in mds:
            if md['datetime'] == dt:
                # found
                return md

        # not found
        md = {'datetime': dt}
        mds.append(md)
        return md

class MonitoringUtility():

    @staticmethod
    def get_metric_setting(setting, key, value):

        for metric in setting.get(key):
            if metric[0] == value:
                break

        return metric

    @staticmethod
    def get_1st_value(metric_setting):

        return metric_setting[3][0][1]

    @staticmethod
    def get_2nd_value(metric_setting):

        return metric_setting[3][1][1]

    @staticmethod
    def get_value(status_setting, number):

        for status in status_setting[3]:
            if status[0] == number:
                break

        return status[1]

    @staticmethod
    def create_hdata(metric):
    
        hdatas = []
        hdata = {'colname': 'datetime', 'width': '120px', 'align': 'center', 'scale': 0}
        hdatas.append(hdata)

        width = ''
        if len(metric[4]) == 1:
            width = '170px'
        elif len(metric[4]) == 2:
            width = '78px'
        # TODO:len(metric[3]) >= 3

        align = ''
        if metric[2] == 1:
            align = 'right'
        elif metric[2] == 2:
            align = 'center'

        for mt in metric[4]:
            hdata = {'colname': mt, 'width': width, 'align': align, 'scale': metric[2]}
            hdatas.append(hdata)

        return hdatas

    @staticmethod
    def create_data(hdatas, mdatas):

        datas = []
        for mdata in mdatas:
            lines = []
            for hdata in hdatas:
                line = {}
                line['name'] = hdata['colname']
                line['value'] = mdata[hdata['colname']]
                lines.append(line)
            datas.append(lines)

        return datas

def slice_list(request):
    logger.info("slice_list user=%s" % request.user)

    # get slice list
    msrc = MSRestClient()
    slices = msrc.get_slice_list(request.user)
    logger.debug("slices=%s" % str(slices))

    extra_context={
            "breadcrumbs": (
                ("Home", reverse("home")),
                ("Monitoring", reverse("m_slice_list")),
            ),
            "slices": slices
    }

    return simple.direct_to_template(
        request,
        template="slice.html",
        extra_context=dict(extra_context.items()),
    )

def slice_detail(request, slice_id):
    logger.info("slice_detail user=%s, slice=%s" % (request.user, slice_id))

    # get topology data
    msrc = MSRestClient()
    topology = msrc.get_topology_list(request.user, slice_id)
    logger.debug("topology=%s" % str(topology))
    if topology['slice'] == None:
        logger.warn("Slice does not exist slice=%s" % (slice_id))
        return HttpResponseRedirect(reverse("m_slice_list"))

    # get slice detail data
    slice_detail = msrc.get_slice_detail(request.user, topology)
    logger.debug("slice_detail=%s" % str(slice_detail))

    extra_context={
            "breadcrumbs": (
                ("Home", reverse("home")),
                ("Monitoring", reverse("m_slice_list")),
                (topology['slice']['name'], reverse("m_slice_detail", args=[slice_id])),
            ),
            "sliceid": slice_id,
            "slicename": topology['slice']['name'],
    }

    return simple.direct_to_template(
        request,
        template="slice_detail.html",
        extra_context=dict(extra_context.items() + slice_detail.items()),
    )

def monitor_sdn(request, resource_id=None):
    logger.info("monitor_sdn user=%s, resource_id=%s" % (request.user, resource_id))

    settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
    extra_context={
        'timezone' : settings.get('monitoring_timezone'),
    }
    template_name = "monitor_sdn.html"

    if resource_id != None:

        # parse resource_id
        param = dict()
        slice_id, param['node_id'], param['node_port'], param['node_location'], param['network'], type = resource_id.split(',')
        logger.info("slice_id=%s, resource_id=%s" % (slice_id, str(param)))

        # setting display resourceid
        node_name = MSRestClient.nodeid_to_name(param['node_id'], type)
        location_name = MSRestClient.nwname_to_name(param['node_location'], param['network'])
        extra_context['resourceid'] = "Selected OpenFlow switch: %s port: %s at %s" % (node_name, param['node_port'], location_name)

        if request.method == "GET":
            form = MonitorSDNForm()
            form.set_fields(settings)

        elif request.method == "POST":
            form = MonitorSDNForm(request.POST)
            form.set_fields(settings)
            if form.is_valid():

                # get metric setting
                metric = MonitoringUtility.get_metric_setting(settings, 'monitoring_sdn_metric', form.cleaned_data['metric'])
                extra_context['graph_scale'] = metric[2]
                extra_context['decimal_point_accuracy'] = 0
                if metric[2] == 1:
                    extra_context['decimal_point_accuracy'] = metric[3][0]
                elif metric[2] == 2:
                    extra_context['ordinal_value'] = metric[3]

                # get monitoring data
                param['monitor'] = 'sdn'
                param['metric'] = metric
                param['timezone'] = form.cleaned_data['timezone']
                param['datefrom'] = form.cleaned_data['datefrom']
                param['dateto'] = form.cleaned_data['dateto']
                param['limit'] = form.cleaned_data['limit']
                param['sliceid'] = slice_id
                logger.info("param: %s" % str(param))
                msrc = MSRestClient()
                mdata = msrc.get_monitoring_data(param)
#                extra_context['monitoringdata'] = mdata
#                logger.debug("monitoringdata=%s" % str(extra_context['monitoringdata']))

                hdata = MonitoringUtility.create_hdata(metric)
                extra_context['hdatas'] = hdata
                extra_context['mdatas'] =  MonitoringUtility.create_data(hdata, mdata)

        # form setting
        extra_context['form'] = form

    return simple.direct_to_template(
        request,
        template=template_name,
        extra_context=dict(extra_context.items())
    )

def monitor_cp(request, resource_id=None):
    logger.info("monitor_cp user=%s, resource_id=%s" % (request.user, resource_id))

    settings = PLUGINLOADER.plugin_settings.get('m_gui').get('mgui')
    extra_context={
        'timezone' : settings.get('monitoring_timezone'),
    }
    template_name = "monitor_cp.html"

    if resource_id != None:

        # parse resource_id
        param = dict()
        slice_id, param['node_id'], param['node_location'], param['network'], type = resource_id.split(',')
        logger.info("slice_id=%s, resource_id=%s" % (slice_id, str(param)))

        # setting display resourceid
        node_name = MSRestClient.nodeid_to_name(param['node_id'], type)
        location_name = MSRestClient.nwname_to_name(param['node_location'], param['network'])
        extra_context['resourceid'] = "Selected %s: %s at %s" % (type, node_name, location_name)

        if request.method == "GET":
            form = MonitorCPForm()
            form.set_fields(settings)

        elif request.method == "POST":
            form = MonitorCPForm(request.POST)
            form.set_fields(settings)
            if form.is_valid():

                # get metric setting
                metric = MonitoringUtility.get_metric_setting(settings, 'monitoring_cp_metric', form.cleaned_data['metric'])
                extra_context['graph_scale'] = metric[2]
                extra_context['decimal_point_accuracy'] = 0
                if metric[2] == 1:
                    extra_context['decimal_point_accuracy'] = metric[3][0]
                elif metric[2] == 2:
                    extra_context['ordinal_value'] = metric[3]

                # get monitoring data
                param['monitor'] = 'cp'
                param['metric'] = metric
                param['timezone'] = form.cleaned_data['timezone']
                param['datefrom'] = form.cleaned_data['datefrom']
                param['dateto'] = form.cleaned_data['dateto']
                param['limit'] = form.cleaned_data['limit']
                param['sliceid'] = slice_id
                logger.info("param: %s" % str(param))
                msrc = MSRestClient()
                mdata = msrc.get_monitoring_data(param)

                hdata = MonitoringUtility.create_hdata(metric)
                extra_context['hdatas'] = hdata
                extra_context['mdatas'] =  MonitoringUtility.create_data(hdata, mdata)

        # form setting
        extra_context['form'] = form

    return simple.direct_to_template(
        request,
        template=template_name,
        extra_context=dict(extra_context.items())
    )

