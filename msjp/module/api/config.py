#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os.path
import ConfigParser

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#set default value.
rest_host = '0.0.0.0'
rest_port = 8080
rest_base = 'monitoring-system'
post_uri = ""
db_addr = '127.0.0.1'
db_port = 3306
db_user = 'root'
db_pass = ''
topology_db = 'monTopologyDB'
mon_data_sdn_db = 'monDataSDNDB'
log_dir = os.path.normpath(os.path.join(BASE_DIR, '../../log'))
log_file = 'monitoring_api.log'
topology_path = ''
debug_flg = 0

#read configuration file.
confFileName = os.path.normpath(os.path.join(BASE_DIR, '../../conf/mon_api.conf'))
confInfo = ConfigParser.ConfigParser()
confInfo.read(confFileName)

#[REST]
if confInfo.has_option('REST', 'rest_hostrest_host'):
    rest_host = confInfo.get('REST', 'rest_host')

if confInfo.has_option('REST', 'rest_port'):
    rest_port = confInfo.getint("REST","rest_port")

if confInfo.has_option('REST', 'rest_base'):
    rest_base = confInfo.get('REST', 'rest_base')

#[URI]
if confInfo.has_option('URI', 'post_uri'):
    post_uri = confInfo.get('URI', 'post_uri')
    #trailing "/" is delete.
    post_uri = post_uri.rstrip("/")
    
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

#[LOG]
if confInfo.has_option('LOG', 'log_dir'):
    log_dir = confInfo.get('LOG', 'log_dir')
    #trailing "/" is delete.
    log_dir = log_dir.rstrip("/")

if confInfo.has_option('LOG', 'log_file'):
    log_file = confInfo.get('LOG', 'log_file')

#[FILE_PATH]
if confInfo.has_option('FILE_PATH', 'topology_path'):
    topology_path = confInfo.get('FILE_PATH', 'topology_path')

#[UTILITY]
if confInfo.has_option('UTILITY','debug'):
    debug_flg = confInfo.getint('UTILITY','debug')
