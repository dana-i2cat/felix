#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import calendar
import logging
import requests
import xmltodict
import pytz
import dateutil.parser
import module.collector.config as config
import module.common.const as const
import module.common.util as util
from datetime import datetime
from module.common.topologydb import *
from module.common.md import post_md
from module.common.tn_md import create_monitoring_data_xml,DBUploader

# constants
COL_NAME = 'monitoring-data(tn)'
POST_URI = config.post_uri + "/" + const.TYPE_MON_TN

# logger.
logger = logging.getLogger(const.MODULE_NAME_COL)

# set data uploader script file path.
db_upld = DBUploader(log_name=const.MODULE_NAME_COL,
                        db_name=config.mon_data_tn_db,
                        db_host=config.db_addr,db_port=config.db_port,
                        db_user=config.db_user,db_pass=config.db_pass)

# set interval.
interval = 0
for module in config.module_list:
    if module['class-name'].split('.')[-1] == 'MonitoringDataTN':
        interval = module['interval']
        break

class MonitoringDataTN():
    def __check_timestamp(self,timestamp,now_time):
        # to replace timestamp with now_time if timestamp is smaller than "now_time - interval"
        if int(timestamp) < int(now_time) - interval:
            return str(now_time)

        return str(timestamp)

    def __get_nsi_monitoring_data(self):
        logger.debug("get monitoring-data from NSI.")
        # HTTP GET monitoring-data from NSI
        res = requests.get(config.nsi_uri, timeout=const.HTTP_TIME_OUT)

        # get Xml root element in the Dictionary type.
        all_nsi_md = dict()
        xd_root = xmltodict.parse(res.text)
        
        # get <reservationIDMaps>
        if not xd_root.has_key(const.NST_TAG_RESERVE_MAPS):
            logger.warn('tag <{0}> is not specified.'.format(const.NST_TAG_RESERVE_MAPS))
            return None
        xd_reservationIDMaps = xd_root[const.NST_TAG_RESERVE_MAPS]
    
        # get <updateTime>
        if not xd_reservationIDMaps.has_key(const.NSI_TAG_UPDATE_TIME):
            logger.warn('tag <{0}> is not specified.'.format(const.NSI_TAG_UPDATE_TIME))
            return None
        # convert the updateTime to UNIXTIME(UTC)
        dt_update_time = dateutil.parser.parse(xd_reservationIDMaps[const.NSI_TAG_UPDATE_TIME]).astimezone(pytz.timezone('UTC'))
        update_time = calendar.timegm(dt_update_time.timetuple())
        logger.debug('update time.({0}->{1})'.format(xd_reservationIDMaps[const.NSI_TAG_UPDATE_TIME],update_time))

        # get <reservationIDMap>
        if not xd_reservationIDMaps.has_key(const.NST_TAG_RESERVE_MAP):
            logger.warn('tag <{0}> is not specified.'.format(const.NST_TAG_RESERVE_MAP))
            return None

        for xd_reservationIDMap in util.to_array(xd_reservationIDMaps[const.NST_TAG_RESERVE_MAP]):
            # get <resourceSet>
            if not xd_reservationIDMap.has_key(const.NST_TAG_RESOURCE_SET):
                logger.warn('tag <{0}> is not specified.'.format(const.NST_TAG_RESOURCE_SET))
                continue

            for xd_resourceSet in util.to_array(xd_reservationIDMap[const.NST_TAG_RESOURCE_SET]):
                # get <networkResource>
                if not xd_resourceSet.has_key(const.NST_TAG_NW_RESOURCE):
                    logger.warn('tag <{0}> is not specified.'.format(const.NST_TAG_NW_RESOURCE))
                    continue
                xd_networkResource = xd_resourceSet[const.NST_TAG_NW_RESOURCE]

                # check <globalReservationId>
                if not xd_networkResource.has_key(const.NSI_TAG_LINK_ID):
                    logger.warn('tag <{0}> is not specified.'.format(const.NSI_TAG_LINK_ID))
                    continue
                logger.debug(xd_networkResource[const.NSI_TAG_LINK_ID])

                # check <dataPlaneState>
                if not xd_networkResource.has_key(const.NSI_TAG_STATE):
                    logger.warn('tag <{0}> is not specified.'.format(const.NSI_TAG_STATE))
                    continue

                md_dict = {'timestamp':update_time}
#                 # get <provisionState>
#                 if xd_networkResource[const.NSI_TAG_STATE] == 'PROVISIONED':
#                     md_dict['status'] = const.MD_STATUS_UP
#                 else:
#                     md_dict['status'] = const.MD_STATUS_DOWN

                # get <dataPlaneState>isAct=false, ver=0, isConsistent=true</dataPlaneState>
                # create status dict.
                # e.g. state_list=[[dictisAct,false], [ver,0], [isConsistent,true]]
                state_list = [status_value_list.split("=") for status_value_list in xd_networkResource[const.NSI_TAG_STATE].split(",")]
                logger.debug(state_list)

                # e.g. status_dict={isAct:True, ver:0, isConsistent:true}
                state_dict = dict(state_list)
                logger.debug(state_dict)
                if not state_dict.has_key(const.NSI_ELM_STATE):
                    logger.warn('element[{0}] is not found.'.format(const.NSI_ELM_STATE))
                    continue

                if state_dict[const.NSI_ELM_STATE].lower() == 'true':
                    md_dict['status'] = const.MD_STATUS_UP
                else:
                    md_dict['status'] = const.MD_STATUS_DOWN
                all_nsi_md[xd_networkResource[const.NSI_TAG_LINK_ID]] = md_dict

        logger.debug(all_nsi_md)
        return all_nsi_md

    def __get_monitoring_data(self,all_nsi_md,link_name,now_time):
        logger.debug("get monitoring-data.")
 
        # find NSI-monitoring-data dict.
        if not all_nsi_md.has_key(link_name):
            return None
        md_dict = all_nsi_md[link_name]
        val_list = list()
        val_dict = dict()
        val_dict['status'] = md_dict['status']
        val_dict['timestamp'] = self.__check_timestamp(md_dict['timestamp'],now_time)
        val_list.append(val_dict)

        res_dict = {'link_name':link_name,'val_list':val_list}
        return res_dict

    def main(self):
        # get now time.(UTC:0)
        now_time = calendar.timegm(datetime.utcnow().timetuple())
        try:
            print(COL_NAME + ' -start-')
            logger.info(COL_NAME + ' -start-')
           
            # open topology database connection.
            tpldb_setup()

            # get all of the monitoring-data from NSI.
            all_nsi_md = self.__get_nsi_monitoring_data()

            # get all of the TN-link from DB.
            link_list = get_all_tn_link()

            all_md_list = []
            for link in link_list:
                # get monitoring-data from NSI.
                link_name = link.link_name
                md_dict = self.__get_monitoring_data(all_nsi_md,link_name,now_time)
                if not md_dict:
                    logger.debug('monitoring-data is no data.(link={0})'.format(link_name))
                    continue
                md_dict['network_type'] = link.network.type
                md_dict['network_name'] = link.network_name
                md_dict['link_type'] = link.type
                ### md_dict={network_type:slice,network_name:xxx,
                ###             link_type:tn,link_name:xxx,val_list:list(val_dict[param_name:value])}
                logger.debug(md_dict)
                all_md_list.append(md_dict)
 
            if not all_md_list:
                logger.debug('monitoring-data is no data.(all TN-link)')
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
            # close topology database connection.
            tpldb_close()
            logger.info(COL_NAME + ' -end-')
            print(COL_NAME + ' -end-')
    
        return
