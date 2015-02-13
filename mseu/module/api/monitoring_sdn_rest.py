#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import module.api.config as config
import module.common.const as const
import module.common.util as util
from xml.etree.ElementTree import Element,SubElement
from bottle import route, request, HTTPResponse
from module.common.topologydb import *
from module.common.md import post_md,search_target_table,DBHandle
from module.common.sdn_md import DBUploader

# constants
BASE_URI = '/' + config.rest_base + '/' + const.REST_MONITORING
POST_URI = config.post_uri + "/" + const.TYPE_MON_SDN

# logger.
logger = logging.getLogger(const.MODULE_NAME_API)

# set data uploader script file path.
db_upld = DBUploader(log_name=const.MODULE_NAME_API,
                        db_name=config.mon_data_sdn_db,
                        db_host=config.db_addr,db_port=config.db_port,
                        db_user=config.db_user,db_pass=config.db_pass)

@route(BASE_URI + '/' + const.TYPE_MON_SDN, method='POST')
@route(BASE_URI + '/' + const.TYPE_MON_SDN + '/', method='POST')
def monitoring_sdn_post():
    logger.info('POST monitoring-data({0}).'.format(const.TYPE_MON_SDN))
    try:
        # open topology database connection.
        tpldb_setup()

        # get request body.(xml message.)
        param_list=request.body
        param_string=""
        for row in param_list:
            param_string += row
        if not param_string:
            logger.warn('no message.')
            return HTTPResponse("POST monitoring-data({0}) error.(request body is empty.)"
                                .format(const.TYPE_MON_SDN), status=400)
        logger.debug(param_string)

        # upload all monitoring-data to DB.
        mon_data_dict = db_upld.upload_monitoring_data_all(param_string)
        if not mon_data_dict:
            return HTTPResponse("POST monitoring-data({0}) error.(parse monitoring-data xml error.)"
                                .format(const.TYPE_MON_SDN), status=400)
        
        # forwarding master-monitoring-server
        if mon_data_dict[const.XML_ATTR_FWD] == True:
            logger.debug('forward monitoring-data.(post_uri={0})'.format(POST_URI))
            res_flg,res = post_md(POST_URI,param_string,'no')
            if res_flg is False:
                logger.error('forward monitoring-data error.')
            if res:
                logger.debug("HTTP Response({0}):{1}".format(res.status_code,res.text))
                
    except Exception:
        logger.exception('POST monitoring-data({0}) error.'.format(const.TYPE_MON_SDN))
        return HTTPResponse("POST monitoring-data({0}) error."
                            .format(const.TYPE_MON_SDN), status=500)

    finally:
        # close topology database connection.
        tpldb_close()

    return

@route(BASE_URI + '/' + const.TYPE_MON_SDN + '/<topology_type>/', method='GET')
def monitoring_sdn_get(topology_type=""):
    logger.info('GET monitoring-data({0}).'.format(const.TYPE_MON_SDN))

    # database handle.
    db_handle = DBHandle()
    try:
        # open topology database connection.
        tpldb_setup()     

        # create <monitoring-data>
        xml_mon_data = Element(const.XML_TAG_MON_DATA)
        
        # topology_type==[physical | slice]
        logger.debug('topology type=' + topology_type)
        
        # param_type_list==[status | in_bps | etc...]
        param_type_list = request.query.getall(const.HTTP_GET_OPT_TYPE)
        if param_type_list:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_TYPE +')=' + str(param_type_list))
    
        # get HTTP GET option.
        param_topol = request.query.get(const.HTTP_GET_OPT_TOPOL)
        if param_topol:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_TOPOL +')=' + param_topol)
    
        param_node = request.query.get(const.HTTP_GET_OPT_NODE)
        if param_node:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_NODE +')=' + param_node)
    
        param_port = request.query.get(const.HTTP_GET_OPT_PORT)
        if param_port:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_PORT +')=' + param_port)
        
        param_stime = request.query.get(const.HTTP_GET_OPT_STIME)
        if param_stime:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_STIME +')=' + param_stime)
        
        param_etime = request.query.get(const.HTTP_GET_OPT_ETIME)
        if param_etime:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_ETIME +')=' + param_etime)
        
        param_limit = request.query.get(const.HTTP_GET_OPT_LMT)
        if param_limit:
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_LMT +')=' + param_limit)
        else:
            # set the default value if not specified.
            param_limit = str(const.DEFAULT_LIMIT)
            logger.debug('HTTP GET option ('+ const.HTTP_GET_OPT_LMT +')=default value(' + param_limit +')')

        # required check.(topology_type)
        if not topology_type == const.TYPE_NW_PHYSICAL and \
            not topology_type == const.TYPE_NW_SLICE:

            logger.warn('topology type is invalid. ('+ topology_type +')')
            return HTTPResponse("GET monitoring-data({0}) error.(topology type({1}) is invalid.)"
                                .format(const.TYPE_MON_SDN,topology_type), status=400)

        # required check.(HTTP GET option)
        if not param_type_list:
            logger.warn('Required HTTP GET option({0}) have not been set.'.format(const.HTTP_GET_OPT_TYPE))
            return HTTPResponse("GET monitoring-data({0}) error.(Required HTTP GET option({1}) not specified.)"
                                .format(const.TYPE_MON_SDN,const.HTTP_GET_OPT_TYPE), status=400)
        
        if not param_stime:
            logger.warn('Required HTTP GET option({0}) have not been set.'.format(const.HTTP_GET_OPT_STIME))
            return HTTPResponse("GET monitoring-data({0}) error.(Required HTTP GET option({1}) not specified.)"
                                .format(const.TYPE_MON_SDN,const.HTTP_GET_OPT_STIME), status=400)

        if not param_etime:
            logger.warn('Required HTTP GET option({0}) have not been set.'.format(const.HTTP_GET_OPT_ETIME))
            return HTTPResponse("GET monitoring-data({0}) error.(Required HTTP GET option({1}) not specified.)"
                                .format(const.TYPE_MON_SDN,const.HTTP_GET_OPT_ETIME), status=400)

        # required check.(HTTP GET option:topology)
        nw_list = []
        if not param_topol:
            # If the topology type is 'slice', topology(sliceID) is required
            if topology_type == const.TYPE_NW_SLICE:
                logger.warn('Required HTTP GET option({0}) have not been set.'.format(const.HTTP_GET_OPT_TOPOL))
                return HTTPResponse("GET monitoring-data({0}) error.(Required HTTP GET option({1}) not specified.)"
                                    .format(const.TYPE_MON_SDN,const.HTTP_GET_OPT_TOPOL), status=400)
            
            # If the topology type is 'physical',target all network.
            elif topology_type == const.TYPE_NW_PHYSICAL:
                nw_list = get_all_network(const.TYPE_NW_PHYSICAL)

            # Without network specified, if the node is specified, the value of the node are ignored.
            param_node = None
        else:
            tmp_nw = Network.query.filter(Network.network_name == param_topol).first()
            if tmp_nw:
                nw_list.append(tmp_nw)
       
        # parameter check.(HTTP GET option:node)
        if not param_node:
            # Without node specified, if the port is specified, the value of the port are ignored.
            param_port = None

        # search target table name.
        tbl_name_list = search_target_table(logger,int(param_stime),int(param_etime),config.mon_data_sdn_db)
    
        # add <topology_list>
        xml_topol_list = SubElement(xml_mon_data, const.XML_TAG_TOPOL_LIST)

        # connect to the database.
        db_con = db_handle.connect(config.mon_data_sdn_db,config.db_addr
                                   ,config.db_port,config.db_user,config.db_pass)

        for nw in nw_list:
            # add <topology type=topology_type name='xxx'>
            xml_topol = SubElement(xml_topol_list, const.XML_TAG_TOPOL,
                                    {const.XML_ATTR_TYPE:nw.type,const.XML_ATTR_NAME:nw.network_name})

            node_list = []
            if not param_node:
                # not specified. cover all of the node.
                node_list = get_all_sw(nw)
            else:
                tmp_node = Node.query.filter(Node.node_name == param_node)\
                             .filter(Node.network_name == nw.network_name)\
                             .filter(Node.type == const.TYPE_NODE_SW).first()
                if tmp_node:
                    node_list.append(tmp_node)
    
            for node in node_list:
                # add <node id='xxx' type='switch'>
                xml_node = SubElement(xml_topol, const.XML_TAG_NODE,
                                        {const.XML_ATTR_ID:node.node_name,
                                         const.XML_ATTR_TYPE:node.type
                                            })
        
                if_list = []
                if not param_port:
                    # not specified. cover all of the port.
                    if_list = get_all_if(node)
                else:
                    tmp_if = InterFace.query.filter(InterFace.idNode == node.id)\
                             .filter(InterFace.port == param_port).first()
                    if tmp_if:
                        if_list.append(tmp_if)

                for interface in if_list:
                    # add <port num=param_port>
                    xml_port = SubElement(xml_node, const.XML_TAG_PORT, {const.XML_ATTR_NUM:interface.port})
                
                    for param_type in param_type_list:
                        # add <parameter type=param_type>
                        xml_param = SubElement(xml_port, const.XML_TAG_PARAM, {const.XML_ATTR_TYPE:param_type})

                        # no data in the search time-range.
                        if not tbl_name_list:
                            continue

                        # search database.(metaID)
                        sql = "(SELECT metaID FROM metaData " \
                               + "WHERE network_name='{0}' AND node_name='{1}' AND port='{2}' AND type='{3}')"\
                                    .format(nw.network_name,node.node_name,interface.port,param_type)
                        logger.debug(sql)
                        db_con.execute(sql)
                         
                        res_metaid = db_con.fetchone()
                        if res_metaid:
                            metaid = res_metaid['metaID']
                        else:
                            continue
                
                        # search database.(data)
                        sql_base = "(SELECT timestamp,value FROM {0} WHERE metaID={1}"\
                                    + " AND timestamp >= {0}".format(param_stime)\
                                    + " AND timestamp <= {0})".format(param_etime)
                        sql_list = []
                        for tbl_name in tbl_name_list:
                            sql_list.append(sql_base.format(tbl_name,metaid))
                        sql = " UNION ".join(sql_list)
                        sql += " ORDER BY timestamp DESC LIMIT " + param_limit
                        logger.debug(sql)
                        db_con.execute(sql)
                        res_mon_data = db_con.fetchall()
                  
                        for mon_data in res_mon_data:
                            # add <value timestamp=mon_data["timestamp"]>
                            xml_value = SubElement(xml_param, const.XML_TAG_VAL, {const.XML_ATTR_TIME_STAMP:str(mon_data["timestamp"])})
                            # add <value>mon_data["value"]</value>
                            xml_value.text = str(mon_data["value"])

    except Exception:
        logger.exception('GET monitoring-data({0}) error.'.format(const.TYPE_MON_SDN))
        return HTTPResponse("GET monitoring-data({0}) error."
                            .format(const.TYPE_MON_SDN), status=500)

    finally:
        # close monitoring database connection.
        db_handle.close()

        # close topology database connection.
        tpldb_close()     

    return util.prettify(xml_mon_data)
