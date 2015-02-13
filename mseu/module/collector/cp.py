#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import calendar
import logging
import module.collector.config as config
import module.common.const as const
from datetime import datetime
from module.common.topologydb import *
from module.common.md import post_md
from module.common.cp_md import create_monitoring_data_xml,DBUploader
from module.common.util import to_array
from pyzabbix import ZabbixAPI

# constants
COL_NAME = 'monitoring-data(cp)'
POST_URI = config.post_uri + "/" + const.TYPE_MON_CP

# logger.
logger = logging.getLogger(const.MODULE_NAME_COL)

# set data uploader script file path.
db_upld = DBUploader(log_name=const.MODULE_NAME_COL,
                        db_name=config.mon_data_cp_db,
                        db_host=config.db_addr,db_port=config.db_port,
                        db_user=config.db_user,db_pass=config.db_pass)

# set interval.
interval = 0
for module in config.module_list:
    if module['class-name'].split('.')[-1] == 'MonitoringDataCP':
        interval = module['interval']
        break

class MonitoringDataCP():
    def __check_timestamp(self,timestamp,now_time,ts_type):
        # If timestamp_type is 1.
        if ts_type == const.TYPE_TS_REP:
            # to replace timestamp with now_time if timestamp is smaller than "now_time - interval"
            if int(timestamp) < int(now_time) - interval:
                return str(now_time)

        return str(timestamp)

    def __get_monitoring_data(self,zapi,node_name,node_type,now_time):
        logger.debug("get monitoring-data.")
 
        # Query item[status]
        item_sts = ""
        target_item_list = None
        if node_type == const.TYPE_NODE_SRV:
            item_sts = const.ZBX_SRV_STS
            target_item_list = config.cp_mon_item_srv_list
        elif node_type == const.TYPE_NODE_VM:
            item_sts = const.ZBX_VM_STS
            target_item_list = config.cp_mon_item_vm_list
            
        item_sts = item_sts + '[{0}]'.format(node_name)
        items = zapi.item.get(output=['hostid','lastclock','lastvalue']
                            ,filter={"key_":item_sts})

        if not len(items):
            logger.warn('item is not found.({0})'.format(item_sts))
            return None
        elif len(items) != 1:
            logger.warn('item is not one.({0})'.format(item_sts))
            return None
        logger.debug(items)

        # Print out each datapoint
        val_list = list()
        for item in items:
            val_dict = dict()
            val_dict['status'] = item['lastvalue']
            val_dict['timestamp'] = self.__check_timestamp(item['lastclock'],now_time,const.TYPE_TS_REP)
            val_list.append(val_dict)
            hostid = item['hostid']

        for target_item in target_item_list:
            # Query item[set in the configuration file values]
            items = zapi.item.get(output=['lastclock','lastvalue']
                                ,filter={"hostid":hostid,"key_":target_item['item-name']})
    
            # If nothing was found, try getting it from history
            if not len(items):
                logger.warn('item is not found.({0})'.format(target_item['item-name']))
                continue
            elif len(items) != 1:
                logger.warn('item is not one.({0})'.format(item_sts))                
            logger.debug(items)
    
            # Print out each datapoint
            for item in items:
                val_dict = dict()
                val_dict[target_item['data-name']] = item['lastvalue']
                val_dict['timestamp'] = self.__check_timestamp(item['lastclock'],now_time,target_item['ts-type'])
     
                val_list.append(val_dict)

        res_dict = {'node_name':node_name,'node_type':node_type,'val_list':val_list}
        return res_dict   

    def main(self):
        # now monitoring timesamp(etime)
        now_time = 0
        try:
            print(COL_NAME + ' -start-')
            logger.debug(COL_NAME + ' -start-')
            
            # get now time.(UTC:0)
            now_time = calendar.timegm(datetime.utcnow().timetuple())
            
            # Login to the Zabbix API
            zapi = ZabbixAPI(config.zabbix_uri)
            zapi.login(config.zabbix_user,config.zabbix_pass)

            node_list =list()
            # get all of the VM from DB.
            vm_list = get_all_vm()
            if vm_list:
                node_list.extend(vm_list)

            # get all of the Server from DB.
            srv_list = get_all_srv()
            if srv_list:
                node_list.extend(srv_list)

            all_md_list = []
            for node in node_list:
                # get monitoring-data from Zabbix.
                node_name = node.node_name
                node_type = node.type
                md_dict = self.__get_monitoring_data(zapi,node_name,node_type,now_time)
                if not md_dict:
                    logger.debug('monitoring-data is no data.(node={0},type={1})'.format(node_name,node_type))
                    continue
                md_dict['network_name'] = node.network_name
                md_dict['network_type'] = node.network.type
                ### md_dict={nw_name:xxx,nw_type,node_name:xxx,node_type:server|vm,
                ###             val_list:list(val_dict[param_name:value])}
                logger.debug(md_dict)
                all_md_list.append(md_dict)
 
            if not all_md_list:
                logger.debug('monitoring-data is no data.(all node)')
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
            zapi.logout
            logger.debug(COL_NAME + ' -end-')
            print(COL_NAME + ' -end-')
    
        return
