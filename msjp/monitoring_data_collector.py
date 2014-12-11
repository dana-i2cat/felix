#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import logging
import module.collector.config as config
import module.common.const as const
import module.common.util as util
from apscheduler.schedulers.blocking import BlockingScheduler
from module.common.topologydb import create_metadata
from module.collector.sdn import MonitoringDataSDN

def outlog_confvalue(logger):
    # write the settings to the log file.
    logger.info('----------[settings]---------')
    logger.info('post_uri={0}'.format(config.post_uri))
    logger.info('sequel_service_uri={0}'.format(config.sequel_service_uri))
    logger.info('db_addr={0}'.format(config.db_addr))
    logger.info('db_port={0}'.format(config.db_port))
    logger.info('db_user={0}'.format(config.db_user))
    logger.info('db_pass={0}'.format(config.db_pass))
    logger.info('topology_db={0}'.format(config.topology_db))
    logger.info('mon_data_sdn_db={0}'.format(config.mon_data_sdn_db))
    for mon_item in config.mon_item_list:
        logger.info('monitoring-data-name={0} aggregate-type={1}'.format(mon_item['data-name'],mon_item['agg-type']))       
    logger.info('log_dir={0}'.format(config.log_dir))
    logger.info('log_file={0}'.format(config.log_file))
    logger.info('interval={0}'.format(config.interval))
    logger.info('aggregate_flg={0}'.format(config.aggregate_flg))
    logger.info('debug_flg={0}'.format(config.debug_flg))
    logger.info('-----------------------------')

# scheduler
sched = BlockingScheduler()

#monitoring-data(SDN) collector
sdn_collector = MonitoringDataSDN()

@sched.scheduled_job('interval', seconds=config.interval)
def main_loop():
    try:
        #collect monitoring-data(SDN)
        sdn_collector.main()

    except Exception:
        logger.exception(const.MODULE_NAME_COL)

    return

# Main function.
if __name__ == '__main__':
    start_msg = '{0} starting up (interval = {1}sec)...'.format(const.MODULE_NAME_COL,str(config.interval))

    # check log directory.
    if not os.path.exists(config.log_dir) :
        os.mkdir(config.log_dir)

    # make logfile name(full path).
    logfile = config.log_dir + '/' + config.log_file

    # create logger(monitoring_data_collector).
    logger = util.init_logger(const.MODULE_NAME_COL,logfile)
    if not logger:
        sys.exit(1)

    # create logger(scheduler).
    util.init_logger("apscheduler.scheduler",logfile)

    if config.debug_flg == 1 :
        logger.setLevel(logging.DEBUG)
        logger.info('(debug mode)' + start_msg)
    else :
        logger.setLevel(logging.INFO)
        logger.info(start_msg)

    # write the settings to the log file.
    outlog_confvalue(logger)

    # create topologyDB meta data.
    create_metadata(config.topology_db,config.db_addr
                                    ,config.db_port,config.db_user,config.db_pass,config.debug_flg)

    # run.
    print(start_msg)
    print('Hit Ctrl-C to quit.')
  
    sched.start()
