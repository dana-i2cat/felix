#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os.path
import ConfigParser
import module.common.util as util

# constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# set default value.
default_config = {
    'rest_host' : '0.0.0.0',
    'rest_port' : '8448',
    'rest_base' : 'monitoring-system',
    'post_uri' : '',
    'sequel_service_uri' : 'http://127.0.0.1:8015/perfSONAR_PS/services/sequel',
    'db_addr' : '127.0.0.1',
    'db_port' : '3306',
    'db_user' : 'root',
    'db_pass' : '',
    'topology_db' : 'fms__monitoring_topology',
    'mon_data_sdn_db' : 'fms__monitoring_sdnrm',
    'mon_data_se_db' : 'fms__monitoring_serm',
    'mon_data_cp_db' : 'fms__monitoring_crm',
    'mon_data_tn_db' : 'fms__monitoring_tnrm',
    'log_dir' : os.path.normpath(os.path.join(BASE_DIR, '../../log')),
    'log_file' : 'monitoring_api.log',
    'debug' : '0'
}

# read configuration file.
confFileName = os.path.normpath(os.path.join(BASE_DIR, '../../conf/mon_api.conf'))
confInfo = ConfigParser.SafeConfigParser(default_config)
confInfo.read(confFileName)

# [REST]
rest_host = util.get_config_param(confInfo,'REST', 'rest_host')
rest_port = util.getint_config_param(confInfo,"REST","rest_port")
rest_base = util.get_config_param(confInfo,'REST', 'rest_base')

# [URI]
post_uri = util.get_config_param(confInfo,'URI', 'post_uri')
    
# [DATABASE]
db_addr = util.get_config_param(confInfo,'DATABASE', 'db_addr')
db_port = util.getint_config_param(confInfo,"DATABASE","db_port")
db_user = util.get_config_param(confInfo,'DATABASE', 'db_user')
db_pass = util.get_config_param(confInfo,'DATABASE', 'db_pass')
topology_db = util.get_config_param(confInfo,'DATABASE', 'topology_db')
mon_data_sdn_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_sdn_db')
mon_data_se_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_se_db')
mon_data_cp_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_cp_db')
mon_data_tn_db = util.get_config_param(confInfo,'DATABASE', 'mon_data_tn_db')

# [LOG]
log_dir = util.get_config_param(confInfo,'LOG', 'log_dir')
log_file = util.get_config_param(confInfo,'LOG', 'log_file')

# [UTILITY]
debug_flg = util.getint_config_param(confInfo,'UTILITY','debug')
