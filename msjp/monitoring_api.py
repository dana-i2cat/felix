#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.append(os.path.normpath(os.path.join(BASE_DIR, 'lib')))
import logging
import module.common.const as const
import module.common.util as util
from bottle import run
from module.common.topologydb import create_metadata
from module.api import *

def outlog_confvalue(logger):
    # write the settings to the log file.
    logger.info('----------[settings]---------')
    logger.info('rest_host={0}'.format(config.rest_host))
    logger.info('rest_port={0}'.format(config.rest_port))
    logger.info('rest_base={0}'.format(config.rest_base))
    logger.info('post_uri={0}'.format(config.post_uri))
    logger.info('db_addr={0}'.format(config.db_addr))
    logger.info('db_port={0}'.format(config.db_port))
    logger.info('db_user={0}'.format(config.db_user))
    logger.info('db_pass={0}'.format(config.db_pass))
    logger.info('topology_db={0}'.format(config.topology_db))
    logger.info('mon_data_sdn_db={0}'.format(config.mon_data_sdn_db))
    logger.info('log_dir={0}'.format(config.log_dir))
    logger.info('log_file={0}'.format(config.log_file))
    logger.info('topology_path={0}'.format(config.topology_path))
    logger.info('debug_flg={0}'.format(config.debug_flg))
    logger.info('-----------------------------')

# Main function.
if __name__ == '__main__':
    start_msg = '{0} starting up...'.format(const.MODULE_NAME_API)

    # check log directory.
    if not os.path.exists(config.log_dir) :
        os.mkdir(config.log_dir)

    # make logfile name(full path).
    logfile = config.log_dir + '/' + config.log_file

    # create logger(monitoring_api).
    if not os.path.exists(config.log_dir) :
        os.mkdir(config.log_dir)
    logfile = config.log_dir + '/' + config.log_file
    logger = util.init_logger(const.MODULE_NAME_API,logfile)
    if not logger:
        sys.exit(1)

    # create topologyDB meta data.
    create_metadata(config.topology_db,config.db_addr
                                    ,config.db_port,config.db_user,config.db_pass,config.debug_flg)

    # run.
    if config.debug_flg == 1 :
        logger.setLevel(logging.DEBUG)
        logger.info('(debug mode)' + start_msg)
        outlog_confvalue(logger)
        run(host=config.rest_host, port=config.rest_port, debug=True)
    else :
        logger.setLevel(logging.INFO)
        logger.info(start_msg)
        outlog_confvalue(logger)
        run(host=config.rest_host, port=config.rest_port, debug=False)
        
