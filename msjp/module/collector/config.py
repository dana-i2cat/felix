#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os.path
import ConfigParser
import module.common.const as const

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#set default value.
post_uri = 'http://127.0.0.1:8080/monitoring-system/monitoring'
sequel_service_uri = 'http://127.0.0.1:8015/perfSONAR_PS/services/sequel'
db_addr = '127.0.0.1'
db_port = 3306
db_user = 'root'
db_pass = ''
topology_db = 'monTopologyDB'
mon_data_sdn_db = 'monDataSDNDB'
log_dir = os.path.normpath(os.path.join(BASE_DIR, '../../log'))
log_file = 'monitoring_data_collector.log'
interval = 60
aggregate_flg = 1
debug_flg = 0

#read configuration file.
confFileName = os.path.normpath(os.path.join(BASE_DIR, '../../conf/mon_col.conf'))
confInfo = ConfigParser.ConfigParser()
confInfo.read(confFileName)

#[URI]
if confInfo.has_option('URI', 'post_uri'):
    post_uri = confInfo.get('URI', 'post_uri')
    #trailing "/" is delete.
    post_uri = post_uri.rstrip("/")

if confInfo.has_option('URI', 'sequel_service_uri'):
    sequel_service_uri = confInfo.get('URI', 'sequel_service_uri')
    #trailing "/" is delete.
    sequel_service_uri = post_uri.rstrip("/")


#[DATABASE]
if confInfo.has_option('DATABASE', 'db_addr'):
    db_addr = confInfo.get('DATABASE', 'db_addr')

if confInfo.has_option('DATABASE', 'db_port'):
    db_port = confInfo.getint("DATABASE","db_port")

if confInfo.has_option('DATABASE', 'db_user'):
    db_user = confInfo.get('DATABASE', 'db_user')

if confInfo.has_option('DATABASE', 'db_pass'):
    db_pass = confInfo.get('DATABASE', 'db_pass')

if confInfo.has_option('DATABASE', 'topology_db'):
    topology_db = confInfo.get('DATABASE', 'topology_db')

if confInfo.has_option('DATABASE', 'mon_data_sdn_db'):
    mon_data_sdn_db = confInfo.get('DATABASE', 'mon_data_sdn_db')

#[MONITORING-ITEM]
mon_item_list=list()
if confInfo.has_section('MONITORING-ITEM'):
    for item in confInfo.items('MONITORING-ITEM'):
        if len(item) == 2:
            mon_item_dict=dict()
            mon_item_dict['data-name'] = item[0]
            if not (item[1] == const.TYPE_AGG_AVG or item[1] == const.TYPE_AGG_LAST):
                print('(Config)aggregate type is invalid.({0})'.format(item[1]))
                sys.exit(1)
            mon_item_dict['agg-type'] = item[1]
            mon_item_list.append(mon_item_dict)

#[LOG]
if confInfo.has_option('LOG', 'log_dir'):
    log_dir = confInfo.get('LOG', 'log_dir')
    #trailing "/" is delete.
    log_dir = log_dir.rstrip("/")

if confInfo.has_option('LOG', 'log_file'):
    log_file = confInfo.get('LOG', 'log_file')

#[UTILITY]
if confInfo.has_option('UTILITY', 'interval'):
    interval = confInfo.getint('UTILITY','interval')

if interval <= 0:
    print('(Config)interval is invalid.({0})'.format(interval))
    sys.exit(1)

if confInfo.has_option('UTILITY', 'aggregate'):
    aggregate_flg = confInfo.getint('UTILITY','aggregate')

if not (aggregate_flg == 0 or aggregate_flg == 1):
    print('(Config)aggregate is invalid.({0})'.format(aggregate_flg))
    sys.exit(1)

if confInfo.has_option('UTILITY','debug'):
    debug_flg = confInfo.getint('UTILITY','debug')
