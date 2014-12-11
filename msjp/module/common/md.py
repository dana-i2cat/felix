#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import logging
import time
import subprocess
import requests
import xmltodict
import MySQLdb
import module.common.const as const
import module.api.config as config
from xml.etree.ElementTree import Element,SubElement
from module.common.xml_util import prettify,to_array
from module.common.topologydb import *

def search_target_table(logger,stime,etime):
    #database handle.
    db_handle = DBHandle()
    try:
        #connect to the monitoring database.
        db_con = db_handle.connect(config.mon_data_sdn_db,config.db_addr
                                   ,config.db_port,config.db_user,config.db_pass)

        # search target table name.
        tbl_name_list = []                  #database table name list.
        tbl_name_format = "data_%4Y%2m"     #database table name format.
        tmp_tbl_name = None
        tmp_time = stime
        while True:
            tn = time.strftime(tbl_name_format, time.gmtime(int(tmp_time)))
            if tn != tmp_tbl_name:
                #check table exists in the database.
                sql = "show tables like '{0}'".format(tn)
                db_con.execute(sql)               
                res_table = db_con.fetchone()
                if res_table:
                    #add table name list.
                    tbl_name_list.append(tn)
                tmp_tbl_name = tn
                
            if tmp_time > etime:
                break
            tmp_time += const.SEC_ONEDAY #next day.
    except Exception:
        logger.exception('search target table error.')
        raise
    finally:
        #close monitoring database connection.
        db_handle.close()

    return tbl_name_list

def create_monitoring_data_xml(logger,all_md_list):
    try:
        #create <monitoring-data>
        xml_md = Element(const.XML_TAG_MON_DATA)

        #add <topology type='pyshical'>
        xml_topology = SubElement(xml_md, const.XML_TAG_TOPOL,
                                   {const.XML_ATTR_TYPE:const.TYPE_NW_PHYSICAL})
        
        ### md_dict={type:switch,network_name:xxx,node_name:xxx,
        ###             port:xxx,val_list:list(val_dict[param_name:value])}
        for md_dict in all_md_list:
            xml_node = xml_topology.find(".//{0}[@{1}='{2}']"
                                                .format(const.XML_TAG_NODE,const.XML_ATTR_ID,md_dict['node_name']))
            if xml_node is None:
                #add <node id='xxx' type='xxx'>
                xml_node = SubElement(xml_topology, const.XML_TAG_NODE,
                                        {const.XML_ATTR_ID:md_dict['node_name'],
                                         const.XML_ATTR_TYPE:md_dict['type']
                                            })
            xml_port = xml_node.find(".//{0}[@{1}='{2}']"
                                            .format(const.XML_TAG_PORT,const.XML_ATTR_NUM,md_dict['port']))
            if xml_port is None:
                #add <port num='xxx'>
                xml_port = SubElement(xml_node, const.XML_TAG_PORT,
                                        {const.XML_ATTR_NUM:md_dict['port']})
            
            for val_dict in md_dict['val_list']:
                timestamp = val_dict['timestamp']

                for key, value in val_dict.iteritems():
                    if key == 'timestamp':
                        continue

                    xml_param = xml_port.find(".//{0}[@{1}='{2}']"
                                                    .format(const.XML_TAG_PARAM,const.XML_ATTR_TYPE,key))
                    if xml_param is None:
                        #add <parameter type='xxx'>
                        xml_param = SubElement(xml_port, const.XML_TAG_PARAM,
                                                {const.XML_ATTR_TYPE:key})

                    #add <value timestamp='xxx'>xxx</value>
                    SubElement(xml_param, const.XML_TAG_VAL,
                                    {const.XML_ATTR_TIME_STAMP:timestamp}).text = value

    except Exception:
        logger.exception('create_monitoring_data_xml')
        return ''

    return prettify(xml_md)

def parse_monitoring_data_xml(logger,md_xml):
    try:
        mon_data_dict = dict()

        #get Xml root element in the Dictionary type.
        xd_root = xmltodict.parse(md_xml)
        
        #get <monitoring-data>
        if xd_root.has_key(const.XML_TAG_MON_DATA):
            xd_mon_data = xd_root[const.XML_TAG_MON_DATA]
        else:
            logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_MON_DATA))
            return None
    
        #get forward flag.<monitoring-data forward=xxx>
        fwd_flg = False
        if xd_mon_data.has_key('@'+const.XML_ATTR_FWD):
            if xd_mon_data['@'+const.XML_ATTR_FWD].lower() == 'yes':
                fwd_flg = True      
        mon_data_dict[const.XML_ATTR_FWD] = fwd_flg
    
        #get <topology>
        if xd_mon_data.has_key(const.XML_TAG_TOPOL):
            xd_topol = xd_mon_data[const.XML_TAG_TOPOL]
        else:
            logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_TOPOL))
            return None
    
        #get topology type.<topology type=xxx>
        topology_dict = dict()
        mon_data_dict[const.XML_TAG_TOPOL] = topology_dict
        if xd_topol.has_key('@'+const.XML_ATTR_TYPE):
            topol_type = xd_topol['@'+const.XML_ATTR_TYPE]
        else:
            logger.warn('attribute <{0} {1}> is not specified.'\
                        .format(const.XML_TAG_TOPOL,const.XML_ATTR_TYPE))
            return None
        
        if not topol_type == const.TYPE_NW_PHYSICAL and \
            not topol_type == const.TYPE_NW_SLICE:
            logger.warn('attribute <{0} {1}={2}> is invalid value.'\
                        .format(const.XML_TAG_TOPOL,const.XML_ATTR_TYPE,topol_type))
            return None
    
        topology_dict[const.XML_ATTR_TYPE] = topol_type

        #get <node>
        node_dict_list = []
        topology_dict[const.XML_TAG_NODE] = node_dict_list
        if xd_topol.has_key(const.XML_TAG_NODE):
            node_list = to_array(xd_topol[const.XML_TAG_NODE])
        else:
            logger.debug('tag <{0}> is not specified.'.format(const.XML_TAG_NODE))
            return None

        for node in node_list:
            #get node id<node id=xxx>
            node_dict = dict()
            if node.has_key('@'+const.XML_ATTR_ID):
                node_id = node['@'+const.XML_ATTR_ID]
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_NODE,const.XML_ATTR_ID))
                continue
            #get node type<node type=xxx>
            if node.has_key('@'+const.XML_ATTR_TYPE):
                node_type = node['@'+const.XML_ATTR_TYPE]
                if not node_type == const.TYPE_NODE_SW:
                    logger.warn('attribute <{0} {1}={2}> is invalid value.'\
                                .format(const.XML_TAG_NODE,const.XML_ATTR_TYPE,node_type))
                    continue
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_NODE,const.XML_ATTR_TYPE))
                continue
    
            #add node name and node type and network.
            node_dict[const.XML_ATTR_ID] = node_id
            node_dict[const.XML_ATTR_TYPE] = node_type

            #add port dictionary list.
            port_dict_list = []
            node_dict[const.XML_TAG_PORT] = port_dict_list

            #append node dictionary list.
            node_dict_list.append(node_dict)

            #get <port>
            if node.has_key(const.XML_TAG_PORT):
                port_list = to_array(node[const.XML_TAG_PORT])
            else:
                logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_PORT))
                continue
    
            for port in port_list:
                #get port number<port num=xxx>
                port_dict = dict()
                if port.has_key('@'+const.XML_ATTR_NUM):
                    port_num = port['@'+const.XML_ATTR_NUM]
                else:
                    logger.warn('attribute <{0} {1}> is not specified.'\
                                .format(const.XML_TAG_PORT,const.XML_ATTR_NUM))
                    continue
                logger.debug('{0}={1} {2}={3}'\
                             .format(const.XML_TAG_NODE,node_id,const.XML_TAG_PORT,port_num))
                #add port number.
                port_dict[const.XML_ATTR_NUM] = port_num

                #append port dictionary list.
                port_dict_list.append(port_dict)

                #add parameter dictionary list.
                param_dict_list = []
                port_dict[const.XML_TAG_PARAM] = param_dict_list

                #get <parameter>
                if port.has_key(const.XML_TAG_PARAM):
                    param_list = to_array(port[const.XML_TAG_PARAM])
                else:
                    logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_PARAM))
                    continue

                for param in param_list:
                    #get parameter type<parameter type=xxx>
                    param_dict = dict()
                    if param.has_key('@'+const.XML_ATTR_TYPE):
                        param_type = param['@'+const.XML_ATTR_TYPE]
                    else:
                        logger.warn('attribute <{0} {1}> is not specified.'\
                                    .format(const.XML_TAG_PARAM,const.XML_ATTR_TYPE))
                        continue
                    #add parameter type.
                    param_dict[const.XML_ATTR_TYPE] = param_type

                    #add value dictionary list.
                    value_dict_list = []
                    param_dict[const.XML_TAG_VAL] = value_dict_list

                    #append parameter dictionary list.
                    param_dict_list.append(param_dict)

                    #get <value>
                    if param.has_key(const.XML_TAG_VAL):
                        val_list = to_array(param[const.XML_TAG_VAL])
                    else:
                        logger.debug('tag <{0}> is not specified.'.format(const.XML_TAG_VAL))
                        continue

                    for val in val_list:
                        #get value timestamp<value timestamp=xxx>
                        value_dict = dict()
                        if val.has_key('@'+const.XML_ATTR_TIME_STAMP):
                            time_stamp = val['@'+const.XML_ATTR_TIME_STAMP]
                        else:
                            logger.warn('attribute <{0} {1}> is not specified.'\
                                        .format(const.XML_TAG_VAL,const.XML_ATTR_TIME_STAMP))
                            continue
                        #get value text<value>xxx</value>
                        if val.has_key('#text'):
                            val_text = val['#text']
                        else:
                            logger.warn('text <{0}> is not specified.'.format(const.XML_TAG_VAL))
                            continue

                        logger.debug('{0}={1} {2}={3} {4}={5}'
                                     .format(const.XML_ATTR_TYPE,param_type
                                             ,const.XML_ATTR_TIME_STAMP,time_stamp
                                             ,const.XML_TAG_VAL,val_text))

                        #add time stamp and value.
                        value_dict[const.XML_ATTR_TIME_STAMP] = time_stamp
                        value_dict[const.XML_TAG_VAL] = val_text

                        #append value dictionary list.
                        value_dict_list.append(value_dict)
    except Exception:
        logger.exception('parse_monitoring_data_xml')
        raise
    return mon_data_dict

def post_md(post_uri,md_xml,fwd_flg):
    res = None
    try:
        # set forward flag.<monitoring-data forward="xxx">
        xd_root = xmltodict.parse(md_xml)
        xd_root[const.XML_TAG_MON_DATA]['@' + const.XML_ATTR_FWD] = fwd_flg
        res = requests.post(post_uri, data=md_xml)

    except Exception:
        return False,res
    return True,res

class DBUploader:
    logger = None
    base = os.path.dirname(os.path.abspath(__file__))
    data_uploader = os.path.normpath(os.path.join(base, '../../script/uploader.pl'))
    db_name = ""
    db_host = ""
    db_port = ""
    db_user = ""
    db_pass = ""

    def __init__(self,log_name,db_name,db_host,db_port,db_user,db_pass=""):
        #logger.
        self.logger = logging.getLogger(log_name)
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_pass = db_pass

    def __create_value_dict(self,nw,node,port,param_type,ts,val):
        # create value dictionary.
        val_dict = dict()
        val_dict['val_nw']   = nw
        val_dict['val_node'] = node
        val_dict['val_port'] = port
        val_dict['val_type'] = param_type
        val_dict['val_ts']   = ts
        val_dict['val_val']  = val
        return val_dict

    def __upload_monitoring_data(self,**val_dict):
        #upload command.(base string)
        #---example---
        # echo 'timestamp,1414617024,network_name,hoge-nw,node_name,node-hoge,port,3,type,out_bps,value,100' |
        # /hoge/script/uploader.pl -m 'network_name,node_name,port,type'\
        # -d "dbi:mysql:monDataSDNDB:localhost" -u "root" -p "rootroot"
        upld_cmd_uploader = self.data_uploader + " -m '{0},{1},{2},{3}'"\
                                .format(const.DB_COL_NW_NAME,const.DB_COL_NODE_NAME,
                                        const.DB_COL_PORT,const.DB_COL_TYPE)\
                            + " -d \"dbi:mysql:{db_name}:{db_host}:{db_port}\" -u \"{db_user}\" -p \"{db_pass}\""\
                                .format(db_name=self.db_name,
                                        db_host=self.db_host,db_port=self.db_port,
                                        db_user=self.db_user,db_pass=self.db_pass)
    
        #database column name dictionary.
        key_dict = {'key_ts':const.DB_COL_TIME_STAMP,'key_nw':const.DB_COL_NW_NAME
                      ,'key_node':const.DB_COL_NODE_NAME,'key_port':const.DB_COL_PORT
                      ,'key_type':const.DB_COL_TYPE,'key_val':const.DB_COL_VAL}

        # create key and value dictionary.
        key_val_dict = key_dict.copy()
        key_val_dict.update(val_dict)

        #make upload command.
        #---example---
        # echo 'timestamp,1414617024,network_name,hoge-nw,node_name,node-hoge,port,3,type,out_bps,value,100' |
        # /hoge/script/uploader.pl -m 'network_name,node_name,port,type'\
        # -d "dbi:mysql:monDataSDNDB:localhost" -u "root" -p "rootroot"
        upld_cmd = "echo '{key_ts},{val_ts},{key_nw},{val_nw},{key_node},{val_node}"\
                        .format(**key_val_dict)\
                        + ",{key_port},{val_port},{key_type},{val_type},{key_val},{val_val}'"\
                        .format(**key_val_dict)\
                        + " | " + upld_cmd_uploader
        self.logger.debug(upld_cmd)

        #upload the physical monitoring data to DB.
        ret = subprocess.Popen(upld_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = ret.communicate()
        if stdout_data:
            self.logger.debug(stdout_data)
            
        if stderr_data:
            self.logger.warn(stderr_data)
            
        return

    def upload_monitoring_data_all(self,md_xml):
        try:
            #get Xml root element in the Dictionary type.
            self.logger.debug(md_xml)
            mon_data_dict = parse_monitoring_data_xml(self.logger,md_xml)
            if not mon_data_dict:
                self.logger.debug('monitoring-data-dict is null.')
                return None
    
            #get node list
            topol_dict = mon_data_dict[const.XML_TAG_TOPOL]
            node_list = topol_dict[const.XML_TAG_NODE]
            for node in node_list:
                node_id = node[const.XML_ATTR_ID]
                port_list = node[const.XML_TAG_PORT]
    
                for port in port_list:
                    param_list = port[const.XML_TAG_PARAM]
                    port_num = port[const.XML_ATTR_NUM]
    
                    #registered in the database as monitoring data of all the nodes
                    # that are associated with physical and slice.
                    if_list = get_all_target_if(node_id,port_num)
    
                    for interface in if_list:
                        nw_name = interface.node.network_name
              
                        for param in param_list:
                            param_type = param[const.XML_ATTR_TYPE]   
                            val_list = param[const.XML_TAG_VAL]   
                            for val in val_list:
                                time_stamp = val[const.XML_ATTR_TIME_STAMP]
                                val_text = val[const.XML_TAG_VAL]
    
                                #create value dictionary.
                                val_dict = self.__create_value_dict(nw_name,node_id,port_num,param_type,time_stamp,val_text)
        
                                #upload the monitoring data to DB.
                                self.__upload_monitoring_data(**val_dict)
        except Exception:
            self.logger.exception('upload monitoring data error.')
            raise
        return mon_data_dict

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
