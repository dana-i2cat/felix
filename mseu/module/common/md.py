#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import MySQLdb
import requests
import xmltodict
import module.common.const as const
import module.api.config as config

def post_md(post_uri,md_xml,fwd_flg):
    res = None
    try:
        # set forward flag.<monitoring-data forward="xxx">
        xd_root = xmltodict.parse(md_xml)
        xd_root[const.XML_TAG_MON_DATA]['@' + const.XML_ATTR_FWD] = fwd_flg
        res = requests.post(post_uri, data=xmltodict.unparse(xd_root), timeout=const.HTTP_TIME_OUT)

    except Exception:
        return False,res
    return True,res

def search_target_table(logger,stime,etime,db_name):
    # database handle.
    db_handle = DBHandle()
    try:
        logger.debug('search_target_table(db_name={0},stime={1},etime={2})'.format(db_name,stime,etime))
        # connect to the monitoring database.
        db_con = db_handle.connect(db_name,config.db_addr
                                   ,config.db_port,config.db_user,config.db_pass)

        # search target table name.
        tbl_name_list = []                  # database table name list.
        tbl_name_format = "data_%4Y%2m"     # database table name format.
        tmp_tbl_name = None
        tmp_time = stime
        while True:
            tn = time.strftime(tbl_name_format, time.gmtime(int(tmp_time)))
            if tn != tmp_tbl_name:
                # check table exists in the database.
                sql = "show tables like '{0}'".format(tn)
                db_con.execute(sql)               
                res_table = db_con.fetchone()
                if res_table:
                    # add table name list.
                    tbl_name_list.append(tn)
                tmp_tbl_name = tn
                
            if tmp_time > etime:
                break
            tmp_time += const.SEC_ONEDAY # next day.
    except Exception:
        logger.exception('search target table error.')
        raise
    finally:
        # close monitoring database connection.
        db_handle.close()

    logger.debug(tbl_name_list)
    return tbl_name_list

class DBHandle:
    db_con = None
    db_cur = None

    def __del__(self):
        self.close()
 
    def connect(self, db_name,db_addr,db_port,db_user,db_pass=""):
        self.db_con = MySQLdb.connect(
            host = db_addr,
            port = db_port,
            user = db_user,
            passwd = db_pass,
            db = db_name,
            use_unicode = 1
            )
        self.db_cur = self.db_con.cursor(MySQLdb.cursors.DictCursor)
        return self.db_cur
 
    def close(self):
        if self.db_cur:
            self.db_cur.close()
            self.db_cur = None
        if self.db_con:
            self.db_con.close()
            self.db_con = None

    def commit(self):
        if self.db_con:
            self.db_con.commit()
