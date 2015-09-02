#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import signal
import logging
import module.collector.config as config
import module.common.const as const
import module.common.util as util
from apscheduler.schedulers.blocking import BlockingScheduler
from module.common.topologydb import *

def outlog_confvalue(logger):
    # write the settings to the log file.
    logger.info('----------[settings]---------')
    logger.info('post_uri={0}'.format(config.post_uri))
    logger.info('sequel_service_uri={0}'.format(config.sequel_service_uri))
    logger.info('nsi_uri={0}'.format(config.nsi_uri))
    logger.info('db_addr={0}'.format(config.db_addr))
    logger.info('db_port={0}'.format(config.db_port))
    logger.info('db_user={0}'.format(config.db_user))
    logger.info('db_pass={0}'.format(config.db_pass))
    logger.info('topology_db={0}'.format(config.topology_db))
    logger.info('mon_data_sdn_db={0}'.format(config.mon_data_sdn_db))
    logger.info('mon_data_se_db={0}'.format(config.mon_data_se_db))
    logger.info('mon_data_cp_db={0}'.format(config.mon_data_cp_db))
    logger.info('mon_data_tn_db={0}'.format(config.mon_data_tn_db))
    logger.info('zabbix_uri={0}'.format(config.zabbix_uri))
    logger.info('zabbix_user={0}'.format(config.zabbix_user))
    logger.info('zabbix_pass={0}'.format(config.zabbix_pass))
    logger.info('log_dir={0}'.format(config.log_dir))
    logger.info('log_file={0}'.format(config.log_file))
    logger.info('aggregate_flg={0}'.format(config.aggregate_flg))
    logger.info('debug_flg={0}'.format(config.debug_flg))
    logger.info('----------[monitoring-module]---------')
    for module in config.module_list:
        logger.info('monitoring-module={0} interval={1}'.format(module['class-name'],module['interval']))
    logger.info('----------[ps-sdn-monitoring-item]---------')
    for mon_item in config.ps_sdn_mon_item_list:
        logger.info('monitoring-data-name={0} aggregate-type={1}'.format(mon_item['data-name'],mon_item['agg-type']))
    logger.info('----------[ps-se-monitoring-item]---------')
    for mon_item in config.ps_se_mon_item_list:
        logger.info('monitoring-data-name={0} aggregate-type={1}'.format(mon_item['data-name'],mon_item['agg-type']))
    logger.info('----------[zabbix-cp-monitoring-item(server)]---------')
    for mon_item in config.zabbix_cp_mon_item_srv_list:
        logger.info('monitoring-data-name={0} item-name={1} timestamp-type={2}'.format(mon_item['data-name'],mon_item['item-name'],mon_item['ts-type']))
    logger.info('----------[zabbix-cp-monitoring-item(vm)]---------')
    for mon_item in config.zabbix_cp_mon_item_vm_list:
        logger.info('monitoring-data-name={0} item-name={1} timestamp-type={2}'.format(mon_item['data-name'],mon_item['item-name'],mon_item['ts-type']))
    logger.info('-----------------------------')

# scheduler
sched = BlockingScheduler()

# Main function.
if __name__ == '__main__':
    start_msg = '{0} starting up...'.format(const.MODULE_NAME_COL)
    finish_msg = '{0} shutdown...'.format(const.MODULE_NAME_COL)

    # Do not output KeyboardInterrupt.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
 
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
    sche_logfile = config.log_dir + '/scheduler.log'
    util.init_logger("apscheduler.executors.default",sche_logfile)
    util.init_logger("apscheduler.scheduler",sche_logfile)

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
    logger.info(start_msg)
    print(start_msg)
    print('Hit Ctrl-C to quit.')
  
    try:
        # setup topology database mapper.
        tpldb_setup()

        for module in config.module_list:
            # put out the class name from a full path.
            components = module['class-name'].split('.')
            class_name = components[-1]
            del(components[-1])
    
            # dynamically generate a class.
            import_path = '.'.join(components)
            mod = __import__(import_path,fromlist=[class_name])
            class_def = getattr(mod, class_name)
            obj = class_def()
    
            # add job in scheduler.(object need a main() method)
            sched.add_job(obj.main, 'interval', seconds=module['interval'])

        # start scheduler.
        sched.start()
    except Exception:
        logger.exception('{0} error.'.format(const.MODULE_NAME_COL))

    finally:
        # cleanup topology database mapper.
        cleanup_all()
        logger.info(finish_msg)
        print(finish_msg)
