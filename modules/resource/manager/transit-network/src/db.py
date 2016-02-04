# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tn_rm_delegate import logger
logger.info("db: start")

import reservation

#######################################################
# config
#######################################################
isPersistence = True
mySQLhost = "localhost"
mySQLuser = "root"
mySQLpass = "felix"
mySQLchar = "utf8"
mySQLdb = "tnrm"
mySQLtbl = "allocation"
#######################################################

import MySQLdb
import traceback

mySQLtable = '''
        slice_urn                       varchar(512) NOT NULL,
        resv_urn                        varchar(512) NOT NULL PRIMARY KEY,
        nsi_id                          varchar(512) NOT NULL,
        srcstp                          varchar(1024),
        dststp                          varchar(1024),

        srcvlan                         int,
        dstvlan                         int,
        transvlan                       int,
        geni_operational_status         varchar(80),
        geni_expires                    varchar(80),

        geni_allocation_status          varchar(80),
        geni_sliver_urn                 varchar(1024),
        geni_urn                        varchar(1024),
        geni_error                      varchar(1024),
        geni_action                     varchar(1024),

        start_time                      varchar(80),
        manifest_node                   varchar(1024),
        manifest_link                   varchar(1024),

        INDEX(slice_urn),
        INDEX(resv_urn),
        INDEX(nsi_id)
'''


dict_index = {}
dict_index["slice_urn"] = 0
dict_index["resv_urn"] = 1
dict_index["nsi_id"] = 2
dict_index["srcstp"] = 3
dict_index["dststp"] = 4
dict_index["srcvlan"] = 5
dict_index["dstvlan"] = 6
dict_index["transvlan"] = 7
dict_index["geni_operational_status"] = 8
dict_index["geni_expires"] = 9
dict_index["geni_allocation_status"] = 10
dict_index["geni_sliver_urn"] = 11
dict_index["geni_urn"] = 12
dict_index["geni_error"] = 13
dict_index["geni_action"] = 14
dict_index["start_time"] = 15
dict_index["manifest_node"] = 16
dict_index["manifest_link"] = 17
#dict_index[""] = xx
mySQLtables_items = 18

import types
import datetime
# epoch = datetime.fromtimestamp(0, pytz.timezone('Asia/Tokyo'))
epoch = datetime.datetime.utcfromtimestamp(0)

def unix_time_sec(dt):
    # print type(dt)
    # print type(epoch)
    delta = dt - epoch
    logger.info("timezone=%s" % (dt.tzinfo))
    return int(delta.total_seconds())

class tnrm_db:
    def open(self):
        if self.con is not None:
            logger.error("Rule violation: use database. So TNRM stop now.")
            raise Exception("Rule violation: use database. So TNRM stop now.")

        try:
            self.con = MySQLdb.connect(host = mySQLhost, db = "",
                                       user = mySQLuser, passwd = mySQLpass, 
                                       charset = mySQLchar)
            self.cur = self.con.cursor()
            
            sql = "USE %s" % mySQLdb
            self.cur.execute(sql)
        except Exception as e:
            logger.error("tnrm_db:init: use database:%s, ex=%s" % 
                         (mySQLdb, e))
            
    def close(self):
        if self.con is None:
            loggererror("Rule violation: use database. So TNRM stop now.")
            raise Exception("Rule violation: use database. So TNRM stop now.")

        try:
            if self.con is not None:
                self.con.close()
        except Exception as e:
            logger.error("tnrm_db:init: use database:%s, ex=%s" % 
                         (mySQLdb, e))
        finally:
            self.con = None
            self.cur = None


    def __init__(self):
        try:
            self.tnrm = None
            self.con = MySQLdb.connect(host = mySQLhost, db = "",
                                       user = mySQLuser, passwd = mySQLpass, 
                                       charset = mySQLchar)

            self.cur = self.con.cursor()
            sql = "CREATE DATABASE IF NOT EXISTS %s" % mySQLdb
            # sql = "CREATE DATABASE %s" % mySQLdb
            try:
                self.cur.execute(sql)
            except Exception as e:
                logger.error("tnrm_db:init: create database:%s, ex=%s" % 
                             (mySQLdb, e))

            sql = "USE %s" % mySQLdb
            try:
                self.cur.execute(sql)
            except Exception as e:
                logger.error("tnrm_db:init: use database:%s, ex=%s" % 
                             (mySQLdb, e))

            # sql = "CREATE TABLE %s (%s)" % (mySQLtbl, mySQLtable)
            sql = "CREATE TABLE IF NOT EXISTS %s (%s)" % (mySQLtbl, mySQLtable)
            try:
                self.cur.execute(sql)
                self.cur.execute("COMMIT")
            except Exception as e:
                logger.error("tnrm_db:init: create table:%s, ex=%s" % 
                             (mySQLtable, e))

            # sql = ("ALTER TABLE %s ADD INDEX (%s)" % 
            #        (mySQLtbl, "slice_urn, request_urn, nsi_id"))
            # self.cur.execute(sql)
            # logger.info("tnrm_db:init: create index:%s" % mySQLtable)

            self.con.close()
            self.con = None
            self.cur = None
        except Exception as e:
            logger.error("tnrm_db:init: ex=%s" % e)

    def set_tnrm(self, tnrm):
        if self.tnrm is None:
            self.tnrm = tnrm
        else:
            if self.tnrm != tnrm:
                logger.info("tnrm_db:set_tnrm: *********************duplicate set")

    def insert (self, resv):
        fmt = "INSERT INTO %s VALUES ("

        for i in range(0, mySQLtables_items):
            if i == (mySQLtables_items - 1):
                fmt += "\'%s\')"
            else:
                fmt += "\'%s\', "

        logger.info("tnrm_db:insert: fmt=%s" % fmt)

        trans_vlan = "0"
        if resv.trans_vlan is not None:
            trans_vlan = resv.trans_vlan

        error = resv.error
        if error is not None:
            error = error.replace("\"", "")
            error = error.replace("\'", "")

        sql = (fmt % (
                mySQLtbl,
                #1: slice_urn
                resv.slice_urn,
                #2: resv_urn
                resv.urn,
                #3: nsi_id
                resv.resv_id,
                #4: srcstp
                resv.src_if.felix_stp_id,
                #5: dststp
                resv.dst_if.felix_stp_id,
                #6: srcvlan
                int(resv.src_vlan),
                #7: dstvlan
                int(resv.dst_vlan),
                #8: transvlan
                int (trans_vlan),
                #9: geni_operational_status
                resv.ostatus,
                #10: geni_expires
                resv.end_time,
                #11: geni_allocation_status
                resv.astatus,
                #12: geni_sliver_urn
                resv.gid,
                #13: geni_urn
                resv.slice_urn,
                #14: geni_error
                error,
                #15: geni_action
                resv.action,
                #16: start_time
                resv.start_time,
                #16: manifest_node
                resv.manifest_node,
                #17: manifest_link
                resv.manifest_link 
                ))

        logger.info("tnrm_db:insert: sql=%s" % sql)
        try:
            self.open()
            self.cur.execute(sql)
            self.cur.execute("COMMIT")
        except Exception as e:
            logger.error("tnrm_db:insert: ex=%s" % e)
        finally:
            self.close()

    def update(self, resv):
        fmt = "UPDATE %s SET %s=\"%s\",  %s=\"%s\",  %s=\"%s\",  %s=\"%s\",  %s=\"%s\" WHERE resv_urn=\"%s\""

        error = resv.error
        if error is not None:
            error = error.replace("\"", "")
            error = error.replace("\'", "")

        sql = fmt % (mySQLtbl, 
                     "geni_expires", resv.end_time,
                     "geni_operational_status", resv.ostatus,
                     "geni_allocation_status", resv.astatus,
                     "geni_error", error,
                     "geni_action", resv.action,
                     resv.urn)

        logger.info("tnrm_db:update: sql=%s" % sql)

        try:
            self.open()
            self.cur.execute(sql)
            self.cur.execute("COMMIT")
        except Exception as e:
            logger.error("tnrm_db:restart: ex=%s" % e)
            raise e
        finally:
            self.close()

    def update_time(self, resv):
        fmt = "UPDATE %s SET %s=\"%s\" WHERE resv_urn=\"%s\""
        sql = fmt % (mySQLtbl, 
                     "geni_expires", resv.end_time, resv.urn)

        logger.info("tnrm_db:update: sql=%s" % sql)

        try:
            self.open()
            self.cur.execute(sql)
            self.cur.execute("COMMIT")
        except Exception as e:
            logger.error("tnrm_db:restart: ex=%s" % e)
            raise e
        finally:
            self.close()

    def delete(self, resv):
        fmt = "DELETE FROM %s WHERE resv_urn=\"%s\""
        sql = fmt % (mySQLtbl, resv.urn)

        logger.info("tnrm_db:delete: sql=%s" % sql)

        try:
            self.open()
            self.cur.execute(sql)
            self.cur.execute("COMMIT")
        except Exception as e:
            logger.error("tnrm_db:delete: ex=%s" % e)
            raise e
        finally:
            self.close()

    def restart (self):
        fmt = "SELECT * from %s"
        sql = fmt % mySQLtbl
        logger.info("tnrm_db:select: sql=%s" % sql)

        try:
            self.open()
            self.cur.execute(sql)
            rows = self.cur.fetchall()
        except Exception as e:
            logger.error("tnrm_db:restart: ex=%s" % e)
            raise e
        finally:
            self.close()

        drows = []
        for row in rows:
            d = self.row2dict(row)
            drows.append(d)
            logger.info("tnrm_db:select: row=%s" % self.row2str(d))

            if False:
                pass
                # ep = Endpoint(ep_name, ep_vlantag, node, stp)
                # resv = Reservation(None, d["slice_urn"], d["resv_urn"], None, path, d["geni_expires"], d["start_time"]);

            manifest = reservation.manifest_rspec + d["manifest_node"] + d["manifest_link"] + reservation.close_rspec;

            current_time = datetime.datetime.utcnow()
            ic_time = unix_time_sec(current_time)
            is_datetime = datetime.datetime.strptime(d["start_time"], '%Y-%m-%d %H:%M:%S.%f')
            is_time = unix_time_sec(is_datetime)
            ie_datetime = datetime.datetime.strptime(d["geni_expires"], '%Y-%m-%d %H:%M:%S.%f')
            ie_time = unix_time_sec(ie_datetime)

            # logger.info("start_time:   %s, %d" % (d["start_time"], is_time))
            # logger.info("end_time:     %s, %d" % (d["geni_expires"], ie_time))
            # logger.info("current_time: %s, %d" % (current_time, ic_time))

            # try:
            self.tnrm.re_allocate(
                d["slice_urn"], d["resv_urn"], manifest, is_datetime, 
                ie_datetime, d["nsi_id"], d["transvlan"], 
                d["geni_operational_status"], d["geni_allocation_status"], 
                d["geni_error"], d["geni_action"])
                 
            # except Exception as e:
            # logger.error("restart: ex=%s" % e)
            # d["geni_error"] = d["geni_error"] + ("\n******* restart: ex=%s" % e)
            # raise e
                
        # raise Exception("stop here in restart")

    def row2str (self, d):
        s  = "\n"
        s += ("\tslice_urn=%s\n" % d["slice_urn"])
        s += ("\tresv_urn=%s\n" % d["resv_urn"])
        s += ("\tid=%s\n" % d["nsi_id"])
        s += ("\tsrcstp=%s\n" % d["srcstp"])
        s += ("\tdststp=%s\n" % d["dststp"])
        s += ("\tsrcvlan=%s, dstvlan=%s, transvlan=%s\n" % 
              (d["srcvlan"], d["dstvlan"], d["transvlan"]))
        s += ("\tgeni_operational_status=%s\n" % d["geni_operational_status"])
        s += ("\tgeni_expires=%s\n" % d["geni_expires"])
        s += ("\tgeni_allocation_status=%s\n" % d["geni_allocation_status"])
        s += ("\tgeni_sliver_urn=%s\n" % d["geni_sliver_urn"])
        s += ("\tgeni_urn=%s\n" % d["geni_urn"])
        s += ("\tgeni_error=%s\n" % d["geni_error"])
        s += ("\tgeni_action=%s\n" % d["geni_action"])
        s += ("\tstart_time=%s\n" % d["start_time"])
        # s += ("\tmanifest_node=%s\n" % d["manifest_node"])
        # s += ("\tmanifest_link=%s\n" % d["manifest_link"])

        # if d["geni_error"] is None:
        #     logger.info("************** geni_error is None.")
        # logger.info("tnrm_db:select: row=%s" % s)
        return s

    def row2dict (self, row):
        d = {}
        for n in dict_index.keys():
            s = ""
            if isinstance(row[dict_index[n]], int):
                s = str(row[dict_index[n]])
            if isinstance(row[dict_index[n]], long):
                s = str(row[dict_index[n]])
            elif isinstance(row[dict_index[n]], str):
                s = row[dict_index[n]]
            else:
                s = row[dict_index[n]].encode('utf-8')
                if s == "None":
                    s = None
            d[n] = s
            # logger.info("tnrm_db:row2dict: %s:%s" % (n, s))

        # logger.info("tnrm_db:row2dict: dict=%s" % d)
        return d


def get_db():
    return db

if __name__ == "__main__":
    logger.info("db-main: %s" % traceback.format_exc())
else:
    logger.info("traceback: %s" % traceback.format_exc())
    db = tnrm_db()
    logger.info("db:tnrm_db init done")

#raise Exception("stop here")
