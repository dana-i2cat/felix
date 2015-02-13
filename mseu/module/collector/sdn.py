#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import calendar
import requests
import xmltodict
import logging
import module.collector.config as config
import module.common.const as const
from datetime import datetime
from module.common.topologydb import *
from module.common.md import post_md
from module.common.sdn_md import create_monitoring_data_xml,DBUploader
from module.common.util import to_array

# constants
COL_NAME = 'monitoring-data(sdn)'
POST_URI = config.post_uri + "/" + const.TYPE_MON_SDN

PS_MSG_TEMPLATE = """
<SOAP-ENV:Envelope 
  xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"     
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Header/>
    <SOAP-ENV:Body>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

# logger.
logger = logging.getLogger(const.MODULE_NAME_COL)

# set data uploader script file path.
db_upld = DBUploader(log_name=const.MODULE_NAME_COL,
                        db_name=config.mon_data_sdn_db,
                        db_host=config.db_addr,db_port=config.db_port,
                        db_user=config.db_user,db_pass=config.db_pass)

class MonitoringDataSDN():
    # befor monitoring timesamp(stime)
    before_time = calendar.timegm(datetime.utcnow().timetuple())

    def __create_ps_msg(self,nmwg_msg):
        msg_template = PS_MSG_TEMPLATE
        xd_root = xmltodict.parse(msg_template)
        xd_msg = xmltodict.parse(nmwg_msg)
        xd_root['SOAP-ENV:Envelope']['SOAP-ENV:Body'] = xd_msg
        return xmltodict.unparse(xd_root)

    def __post_sequel_service(self,msg):
        logger.debug(msg)
        post_uri = config.sequel_service_uri + "/snmpmg"
        headers = {'SOAPAction': 'http://ggf.org/ns/nmwg/base/2.0/message/'}
        return requests.post(post_uri, data=msg, headers=headers)

    def __check_ps_res(self,req_name,msg):
        logger.debug(msg)
        xd_root = xmltodict.parse(msg)
        xd_body = xd_root['SOAP-ENV:Envelope']['SOAP-ENV:Body']
        msg_type = xd_body['nmwg:message']['@type']
        if not msg_type == 'ErrorResponse' and not msg_type == 'QueryResponse':
            return True

        if not xd_body['nmwg:message'].has_key('nmwg:metadata'):
            return True

        event_type = xd_body['nmwg:message']['nmwg:metadata']['nmwg:eventType']
        if 'error' in event_type.lower():
            logger.error('{0} error.({1})'.format(req_name,xd_body['nmwg:message']['nmwg:data']['nmwgr:datum']['#text']))
            return False

        return True

    def __get_tblsaffix(self,stime,etime):
        logger.debug("get table-saffix({0}-{1}).".format(stime,etime))
        table_saffix_msg = """
        <nmwg:message
            xmlns:nmwgt="http://ggf.org/ns/nmwg/topology/2.0/"
            xmlns:nmwg="http://ggf.org/ns/nmwg/base/2.0/"
            xmlns:select="http://ggf.org/ns/nmwg/ops/select/2.0/"
            type="TableSuffixRequest">
            <nmwg:metadata id="m1">
                <nmwg:eventType>http://ggf.org/ns/nmwg/sequel/20090610</nmwg:eventType>
                <nmwg:parameter name="stime">{0}</nmwg:parameter>
                <nmwg:parameter name="etime">{1}</nmwg:parameter>
            </nmwg:metadata>
            <nmwg:data metadataIdRef="m1"/>
        </nmwg:message>
        """.format(stime,etime)

        msg = self.__create_ps_msg(table_saffix_msg)
        logger.debug('request perfSONAR')
        res = self.__post_sequel_service(msg)
        logger.debug('response perfSONAR')

        if self.__check_ps_res('TableSaffixRequest',res.text) == False:
            logger.debug('TableSaffixRequest no resqonse text.')
            return None

        xd_root = xmltodict.parse(res.text)
        xd_body = xd_root['SOAP-ENV:Envelope']['SOAP-ENV:Body']
        if not xd_body['nmwg:message']['nmwg:data']:
            logger.debug('TableSaffixRequest no data.')
            return None

        data_list = to_array(xd_body['nmwg:message']['nmwg:data']['sequel:datum'])
        tblsaffix_list = []
        for data in data_list:
            tblsaffix_list.append(data['@value'])

        return tblsaffix_list

    def __get_monitoring_data(self,node_name,port,stime,etime,tblsaffix_list):
        logger.debug("get monitoring-data.")
        sql_metaid = "(SELECT metaID FROM metaData " \
                      + "WHERE node_name='{0}' AND port='{1}')"\
                      .format(node_name,port)
        # search database.(data)
        sql_base = "(SELECT timestamp,{0} FROM {1} WHERE metaID={2}"\
                    + " AND timestamp &gt;= {0}".format(stime)\
                    + " AND timestamp &lt; {0})".format(etime)

        mon_item_list = []
        for mon_item in config.sdn_mon_item_list:
            mon_item_list.append(mon_item['data-name'])
        if not mon_item_list:
            logger.debug('monitoring-item is not specified.')
            return None
        items = ",".join(mon_item_list)

        sql_list = []
        for tblsaffix in tblsaffix_list:
            sql_list.append(sql_base.format(items,'data_'+tblsaffix,sql_metaid))

        if not sql_list:
            logger.debug('sql_list no data.')
            return None

        sql = " UNION ".join(sql_list)
        sql += " ORDER BY timestamp"
        logger.debug(sql)

        query_msg = """
        <nmwg:message
            xmlns:nmwgt="http://ggf.org/ns/nmwg/topology/2.0/"
            xmlns:nmwg="http://ggf.org/ns/nmwg/base/2.0/"
            xmlns:select="http://ggf.org/ns/nmwg/ops/select/2.0/"
        type="QueryRequest">
            <nmwg:metadata id="m1">
                <nmwg:eventType>http://ggf.org/ns/nmwg/sequel/20090610</nmwg:eventType>
                    <nmwg:parameter name="key">timestamp</nmwg:parameter> 
                    <nmwg:parameter name="query">{0}</nmwg:parameter>
                </nmwg:metadata>
            <nmwg:data metadataIdRef="m1"/>
        </nmwg:message>
        """.format(sql)
        msg = self.__create_ps_msg(query_msg)
        logger.debug('request perfSONAR')
        res = self.__post_sequel_service(msg)
        logger.debug('response perfSONAR')
       
        if self.__check_ps_res('QueryRequest',res.text) == False:
            logger.debug('QueryRequest no resqonse text.')
            return None

        xd_root = xmltodict.parse(res.text)
        xd_body = xd_root['SOAP-ENV:Envelope']['SOAP-ENV:Body']

        if not xd_body['nmwg:message']['nmwg:data']:
            logger.debug('QueryRequest no data.')
            return None

        data_list = to_array(xd_body['nmwg:message']['nmwg:data']['nmwg:commonTime'])
        val_list = list()
        for data in data_list:
            val_dict = dict()
            datum_list = to_array(data['sequel:datum'])
            for datum in datum_list:
                if datum['@value']:
                    val_dict[datum['@name']] = datum['@value']

            val_list.append(val_dict)

        res_dict = {'node_name':node_name,'port':port,'val_list':val_list}
        return res_dict
    
    def __aggregate_avg(self,data_name,val_list):
        ### val_list:list(val_dict[param_name:value])}

        total_val = 0
        count = 0
        timestamp = 0
        for val in val_list:
            if not val.has_key(data_name):
                continue
            total_val += int(val[data_name])
            # a final time of timestamp
            if timestamp <  int(val['timestamp']):
                timestamp = int(val['timestamp'])
            count += 1
            
        if  count == 0:
            return None,timestamp

        agg_val = total_val / count

        return agg_val,timestamp

    def __aggregate_last(self,data_name,val_list):
        ### val_list:list(val_dict[param_name:value])}

        last_val = 0
        timestamp = 0
        for val in val_list:
            if not val.has_key(data_name):
                continue
            # a final time of timestamp
            if timestamp <  int(val['timestamp']):
                last_val = val[data_name]
                timestamp = int(val['timestamp'])
        if timestamp == 0:
            return None,timestamp
        return last_val,timestamp

    def __aggregate(self,md_dict,timestamp):
        ### md_dict={type:switch,network_name:xxx,node_name:xxx,
        ###             port:xxx,val_list:list(val_dict[param_name:value])}

        # The Aggregate for each item of monitoring data.
        # Aggregate(average value or last value)
        agg_val_list = []
        agg_val_dict = dict()
        for item_dict in config.sdn_mon_item_list:
            data_name = item_dict['data-name']
            agg_type = item_dict['agg-type']
            logger.debug('data_name={0} agg_type={1}'.format(data_name,agg_type))
            if agg_type == const.TYPE_AGG_AVG:
                # adding the value　and increments the counter.
                agg_val,agg_ts = self.__aggregate_avg(data_name,md_dict['val_list'])

            elif agg_type == const.TYPE_AGG_LAST:
                # Compare the time stamp, to hold the latest value.
                agg_val,agg_ts = self.__aggregate_last(data_name,md_dict['val_list'])

            else :
                logger.warn('aggregate type is invalid.({0})'.format(agg_val))
                continue

            if agg_val is None:
                logger.warn('aggregate value is null.')
                continue

            logger.debug('timestamp={0} agg_val={1}'.format(agg_ts,agg_val))
            # Timestamp is common to all of the aggregate data
            agg_val_dict['timestamp'] = str(agg_ts)
            agg_val_dict[data_name] = str(agg_val)

        # Store a list that Aggregate value exists only one (overwrite)
        agg_val_list.append(agg_val_dict)
        md_dict['val_list'] = agg_val_list

        return md_dict

    def main(self):
        # now monitoring timesamp(etime)
        now_time = 0
        try:
            print(COL_NAME + ' -start-')
            logger.debug(COL_NAME + ' -start-')

            # get now time.(UTC:0)
            now_time = calendar.timegm(datetime.utcnow().timetuple())
            
            # get monitoring-data from SequelService.
            tblsaffix_list = self.__get_tblsaffix(self.before_time,now_time)
            if not tblsaffix_list:
                logger.debug('tblsaffix_list is no data.')
                return

            # get all of the switch-I/F(port) from DB.
            if_list = get_all_sw_if()
            all_md_list = []
            for interface in if_list:
                if interface.node.network.type == const.TYPE_NW_SLICE:
                    logger.debug('(skip)slice interface is not target.')
                    continue
                # get monitoring-data from SequelService.
                node_name = interface.node.node_name
                port = interface.port
                md_dict = self.__get_monitoring_data(node_name,port,self.before_time,now_time,tblsaffix_list)
                if not md_dict:
                    logger.debug('monitoring-data is no data.(node={0},port={1})'.format(node_name,port))
                    continue
                logger.debug(md_dict)

                # aggregate the monitoring-data.
                if config.aggregate_flg == 1:
                    logger.debug('aggregate the monitoring-data.')
                    md_dict = self.__aggregate(md_dict,now_time)
                    logger.debug(md_dict)

                md_dict['type'] = interface.node.type
                md_dict['network_name'] = interface.node.network_name
                ### md_dict={type:switch,network_name:xxx,node_name:xxx,
                ###             port:xxx,val_list:list(val_dict[param_name:value])}
                all_md_list.append(md_dict)

            if not all_md_list:
                logger.debug('monitoring-data is no data.(all interface)')
                return
            # parse monitoring-data-list to monitoring-data-xml.
            md_xml = create_monitoring_data_xml(logger,all_md_list)
            if not md_xml:
                logger.debug('monitoring-data-xml is null.')
                return
            logger.debug(md_xml)

            # upload monitoring-data to DB.
            logger.debug('upload monitoring-data to DB.')
            if not db_upld.upload_monitoring_data_all(md_xml):
                logger.debug('upload monitoring-data is null.')
                return
    
            # post the monitoring-data to the master-monitoring-server.
            logger.debug('post the monitoring-data to the master-monitoring-server.')
            res_flg,res = post_md(POST_URI,md_xml,'yes')
            if res_flg is False:
                logger.error('post monitoring-data error.(post_uri={0})'.format(POST_URI))
            if res:
                logger.debug("HTTP Response({0}):{1}".format(res.status_code,res.text))

        except Exception:
            logger.exception(COL_NAME)
            print(COL_NAME + ' -exception-')
    
        finally:
            self.before_time = now_time
            logger.debug(COL_NAME + ' -end-')
            print(COL_NAME + ' -end-')
    
        return
