#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os.path
import ConfigParser
import module.common.const as const
import module.common.util as util

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# set default value.
default_config = {
    'post_uri' : 'http://127.0.0.1:8080/monitoring-system/monitoring',
    'sequel_service_uri' : 'http://127.0.0.1:8015/perfSONAR_PS/services/sequel',
    'db_addr' : '127.0.0.1',
    'db_port' : '3306',
    'db_user' : 'root',
    'db_pass' : '',
    'topology_db' : 'monTopologyDB',
    'mon_data_sdn_db' : 'monDataSDNDB',
    'mon_data_cp_db' : 'monDataCPDB',
    'zabbix_uri' : 'http://127.0.0.1/zabbix/api_jsonrpc.php',
    'zabbix_user' : 'admin',
    'zabbix_pass' : 'zabbix',
    'monitoring_module' : None,
    'ps_sdn_monitoring_item' : None,
    'snmp_sdn_monitoring_item' : None,
    'zabbix_cp_monitoring_item_server' : None,
    'zabbix_cp_monitoring_item_vm' : None,
    'snmp_cp_monitoring_item_server' : None,
    'snmp_cp_monitoring_item_vm' : None,
    'log_dir' : os.path.normpath(os.path.join(BASE_DIR, '../../log')),
    'log_file' : 'monitoring_data_collector.log',
    'aggregate' : '1',
    'debug' : '0'
}

# read configuration file.
confFileName = os.path.normpath(os.path.join(BASE_DIR, '../../conf/mon_col.conf'))
# confInfo = ConfigParser.ConfigParser()
confInfo = ConfigParser.SafeConfigParser(default_config)
confInfo.read(confFileName)

# [URI]
post_uri = util.get_config_param(confInfo,'URI','post_uri')
sequel_service_uri = util.get_config_param(confInfo,'URI', 'sequel_service_uri')

# [DATABASE]
db_addr = util.get_config_param(confInfo,'DATABASE', 'db_addr')
db_port = util.getint_config_param(confInfo,"DATABASE","db_port")
db_user = util.get_config_param(confInfo,'DATABASE', 'db_user')
db_pass = util.get_config_param(confInfo,'DATABASE', 'db_pass')
topology_db = util.get_config_param(confInfo,'DATABASE', 'topology_db')
mon_data_sdn_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_sdn_db')
mon_data_cp_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_cp_db')

# [ZABBIX]
zabbix_uri = util.get_config_param(confInfo,'ZABBIX', 'zabbix_uri')
zabbix_user = util.get_config_param(confInfo,'ZABBIX', 'zabbix_user')
zabbix_pass = util.get_config_param(confInfo,'ZABBIX', 'zabbix_pass')

# [MONITORING]
module_list=list()
monitoring_module = util.get_config_param(confInfo,'MONITORING', 'monitoring_module')
monitoring_module = util.to_listinlist(monitoring_module)
for item in monitoring_module:
    if len(item) == 2:
        module_dict=dict()
        module_dict['class-name'] = item[0]
        module_dict['interval'] = item[1]
        module_list.append(module_dict)

# perfSonar
ps_sdn_mon_item_list=list()
ps_sdn_monitoring_item = util.get_config_param(confInfo,'MONITORING', 'ps_sdn_monitoring_item')
ps_sdn_monitoring_item = util.to_listinlist(ps_sdn_monitoring_item)
for item in ps_sdn_monitoring_item:
    if len(item) == 2:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        tmp_item = str(item[1])
        if not (tmp_item == const.TYPE_AGG_AVG or tmp_item == const.TYPE_AGG_LAST):
            print('(Config)aggregate type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['agg-type'] = tmp_item
        ps_sdn_mon_item_list.append(mon_item_dict)

# Zabbix
zabbix_cp_mon_item_srv_list=list()
zabbix_cp_monitoring_item_server = util.get_config_param(confInfo,'MONITORING', 'zabbix_cp_monitoring_item_server')
zabbix_cp_monitoring_item_server = util.to_listinlist(zabbix_cp_monitoring_item_server)
for item in zabbix_cp_monitoring_item_server:
    if len(item) == 3:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        mon_item_dict['item-name'] = item[1]
        tmp_item = str(item[2])
        if not (tmp_item == const.TYPE_TS_REP or tmp_item == const.TYPE_TS_NREP):
            print('(Config)timestamp type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['ts-type'] = tmp_item
        zabbix_cp_mon_item_srv_list.append(mon_item_dict)
 
zabbix_cp_mon_item_vm_list=list()
zabbix_cp_monitoring_item_vm = util.get_config_param(confInfo,'MONITORING', 'zabbix_cp_monitoring_item_vm')
zabbix_cp_monitoring_item_vm = util.to_listinlist(zabbix_cp_monitoring_item_vm)
for item in zabbix_cp_monitoring_item_vm:
    if len(item) == 3:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        mon_item_dict['item-name'] = item[1]
        tmp_item = str(item[2])
        if not (tmp_item == const.TYPE_TS_REP or tmp_item == const.TYPE_TS_NREP):
            print('(Config)timestamp type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['ts-type'] = tmp_item
        zabbix_cp_mon_item_vm_list.append(mon_item_dict)

# SNMP
snmp_sdn_mon_item_list = list()
snmp_sdn_monitoring_item = util.get_config_param(confInfo,'MONITORING', 'snmp_sdn_monitoring_item_vm')
snmp_sdn_monitoring_item = util.to_listinlist(snmp_sdn_monitoring_item)
for item in snmp_sdn_monitoring_item:
    if len(item) == 3:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        mon_item_dict['oid'] = item[1]
        tmp_item = str(item[2])
        if not (tmp_item == const.TYPE_AGG_AVG or tmp_item == const.TYPE_AGG_LAST):
            print('(Config)aggregate type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['agg-type'] = tmp_item
        snmp_sdn_mon_item_list.append(mon_item_dict)


snmp_cp_mon_item_srv_list = list()
snmp_cp_monitoring_item_server = util.get_config_param(confInfo,'MONITORING', 'snmp_sdn_monitoring_item_server')
snmp_cp_monitoring_item_server = util.to_listinlist(snmp_sdn_monitoring_item_server)
for item in snmp_sdn_monitoring_item_server:
    if len(item) == 3:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        mon_item_dict['oid'] = item[1]
        tmp_item = str(item[2])
        if not (tmp_item == const.TYPE_TS_REP or tmp_item == const.TYPE_TS_NREP):
            print('(Config)timestamp type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['ts-type'] = tmp_item
        snmp_sdn_mon_item_server_list.append(mon_item_dict)


snmp_cp_mon_item_vm_list = list()
snmp_cp_monitoring_item_vm = util.get_config_param(confInfo,'MONITORING', 'snmp_sdn_monitoring_item_vm')
snmp_cp_monitoring_item_vm = util.to_listinlist(snmp_sdn_monitoring_item_vm)
for item in snmp_sdn_monitoring_item_vm:
    if len(item) == 3:
        mon_item_dict=dict()
        mon_item_dict['data-name'] = item[0]
        mon_item_dict['oid'] = item[1]
        tmp_item = str(item[2])
        if not (tmp_item == const.TYPE_TS_REP or tmp_item == const.TYPE_TS_NREP):
            print('(Config)timestamp type is invalid.({0})'.format(tmp_item))
            sys.exit(1)
        mon_item_dict['ts-type'] = tmp_item
        snmp_sdn_mon_item_vm_list.append(mon_item_dict)




# [LOG]
log_dir = util.get_config_param(confInfo,'LOG', 'log_dir')
log_file = util.get_config_param(confInfo,'LOG', 'log_file')

# [UTILITY]
aggregate_flg = util.getint_config_param(confInfo,'UTILITY','aggregate')
if not (aggregate_flg == 0 or aggregate_flg == 1):
    print('(Config)aggregate is invalid.({0})'.format(aggregate_flg))
    sys.exit(1)

debug_flg = util.getint_config_param(confInfo,'UTILITY','debug')
