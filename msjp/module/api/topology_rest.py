#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import calendar
import xmltodict
import module.api.config as config
import module.common.const as const
import module.common.util as util
from datetime import datetime
from sqlalchemy.orm import join
from sqlalchemy.sql import select
from xml.etree.ElementTree import Element,SubElement
from bottle import route, request, HTTPResponse
from module.common.topologydb import *
from module.common.md import search_target_table,DBHandle

# constants
BASE_URI = '/' + config.rest_base + '/' + const.REST_TOPOL

#logger.
logger = logging.getLogger(const.MODULE_NAME_API)

def parse_link_xml(xd_root):
    link_dict_list = []
    if xd_root.has_key(const.XML_TAG_LINK):
        link_list = util.to_array(xd_root[const.XML_TAG_LINK])
    else:
        logger.debug('no link.')
        return None

    for link in link_list:
        link_dict = dict()

        #get link id<link id=xxx>
        if link.has_key('@'+const.XML_ATTR_ID):
            #add link name.
            link_dict[const.XML_ATTR_ID] = link['@'+const.XML_ATTR_ID]

        #get link type<link type=xxx>
        if link.has_key('@'+const.XML_ATTR_TYPE):
            link_type = link['@'+const.XML_ATTR_TYPE].lower()
        else:
            logger.warn('attribute <{0} {1}> is not specified.'\
                        .format(const.XML_TAG_LINK,const.XML_ATTR_TYPE))
            return None

        # get interface_ref<interface_ref>
        if link.has_key(const.XML_TAG_IF_REF):
            ifref_list = util.to_array(link[const.XML_TAG_IF_REF])
        else:
            logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_IF_REF))
            return None
        
        # interface_ref exist two always
        if len(ifref_list) != 2:
            logger.warn('tag <{0}> exist two always.({1})'
                        .format(const.XML_TAG_IF_REF),len(ifref_list))
            return None
        
        ifref_client_list = []
        link_dict[const.XML_TAG_IF_REF] = ifref_client_list       
        for ifref in ifref_list:
            #get link type<link type=xxx>
            if ifref.has_key('@'+const.XML_ATTR_CLIENT_ID):
                ifref_client_id = ifref['@'+const.XML_ATTR_CLIENT_ID]
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_IF_REF,const.XML_ATTR_CLIENT_ID))
                return None
        
            #add client id.
            ifref_client_list.append( ifref_client_id)
        
        #append link dictionary list.
        link_dict_list.append(link_dict)

        #add link type.
        link_dict[const.XML_ATTR_TYPE] = link_type

        if link_type == const.TYPE_LINK_ABST_SDN:
            # get abstract link.<link>(Recursively call)
            sub_link_dict_list = parse_link_xml(link)
            if sub_link_dict_list:
                link_dict[const.XML_TAG_LINK] = sub_link_dict_list

    return link_dict_list
    
def parse_node_xml(xd_root):
    #get node<node>
    node_dict_list = [] 
    if xd_root.has_key(const.XML_TAG_NODE):
        node_list = util.to_array(xd_root[const.XML_TAG_NODE])
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
            return None
        #get node type<node type=xxx>
        if node.has_key('@'+const.XML_ATTR_TYPE):
            node_type = node['@'+const.XML_ATTR_TYPE].lower()
        else:
            logger.warn('attribute <{0} {1}> is not specified.'\
                        .format(const.XML_TAG_NODE,const.XML_ATTR_TYPE))
            return None

        if node_type == const.TYPE_NODE_SW:
            pass

        elif node_type == const.TYPE_NODE_SE:
            pass

        elif node_type == const.TYPE_NODE_TN:
            pass

        elif node_type == const.TYPE_NODE_SRV:
            # get vm<node>(Recursively call)
            sub_node_dict_list = parse_node_xml(node)
            if sub_node_dict_list:
                node_dict[const.XML_TAG_NODE] = sub_node_dict_list
                
        elif node_type == const.TYPE_NODE_VM:
            pass

        else:
            logger.warn('attribute <{0} {1}={2}> is invalid value.'\
                        .format(const.XML_TAG_NODE,const.XML_ATTR_TYPE,node_type))
            return None

        #add node name and node type.
        node_dict[const.XML_ATTR_ID] = node_id
        node_dict[const.XML_ATTR_TYPE] = node_type

        #get management type and details
        mgmt_dict = dict()
        if node.has_key(const.XML_TAG_MGMT):
            mgmt_list = util.to_array(node[const.XML_TAG_MGMT])
            if len(mgmt_list) > 1:
                logger.warn('more than one management definition. (node id={0})'.format(node_id))
            mgmt = mgmt_list[0]
            if mgmt.has_key('@'+const.XML_ATTR_MGMT_TYPE):
                mgmt_dict[const.XML_ATTR_MGMT_TYPE] = mgmt['@'+const.XML_ATTR_MGMT_TYPE]
            else:
                logger.warn('management definition has no type. (node id={0})'.format(node_id))
            if mgmt.has_key(const.XML_TAG_MGMT_ADDRESS):
                mgmt_dict[const.XML_TAG_MGMT_ADDRESS] = mgmt[const.XML_TAG_MGMT_ADDRESS]
            if mgmt.has_key(const.XML_TAG_MGMT_PORT):
                mgmt_dict[const.XML_TAG_MGMT_PORT] = mgmt[const.XML_TAG_MGMT_PORT]
            if mgmt.has_key(const.XML_TAG_MGMT_AUTH_ID):
                mgmt_dict[const.XML_TAG_MGMT_AUTH_ID] = mgmt[const.XML_TAG_MGMT_AUTH_ID]
            if mgmt.has_key(const.XML_TAG_MGMT_AUTH_PASS):
                mgmt_dict[const.XML_TAG_MGMT_AUTH_PASS] = mgmt[const.XML_TAG_MGMT_AUTH_PASS]

        #add management
        node_dict[const.XML_TAG_MGMT] = mgmt_dict

        #add interface dictionary list.
        if_dict_list = []
        node_dict[const.XML_TAG_IF] = if_dict_list

        #append node dictionary list.
        node_dict_list.append(node_dict)

        #get <interface>
        if not node.has_key(const.XML_TAG_IF):
            logger.debug('no interface.(node_id={0})'.format(node_id))
            continue

        if_list = util.to_array(node[const.XML_TAG_IF])
        for interface in if_list:
            if_dict = dict()
            #get interface id<interface id=xxx>
            if interface.has_key('@'+const.XML_ATTR_ID):
                if_id = interface['@'+const.XML_ATTR_ID]
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_IF,const.XML_ATTR_ID))
                return None

            #get port number<port num=xxx>
            if interface.has_key(const.XML_TAG_PORT):
                if interface[const.XML_TAG_PORT].has_key('@'+const.XML_ATTR_NUM):
                    port_num = interface[const.XML_TAG_PORT]['@'+const.XML_ATTR_NUM]
                else:
                    logger.warn('attribute <{0} {1}> is not specified.'\
                                .format(const.XML_TAG_PORT,const.XML_ATTR_NUM))
                    return None

                #add port number.
                if_dict[const.XML_TAG_PORT] = port_num

            #add interface id.
            if_dict[const.XML_ATTR_ID] = if_id

            #create and append interface dictionary list.
            if_dict_list.append(if_dict)
                
    return node_dict_list

def parse_topology_xml(topology_list_xml):
    try:

        #get Xml root element in the Dictionary type.
        xd_root = xmltodict.parse(topology_list_xml)

        #get <topology_list>
        if xd_root.has_key(const.XML_TAG_TOPOL_LIST):
            xd_topol_list = xd_root[const.XML_TAG_TOPOL_LIST]
        else:
            logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_TOPOL_LIST))
            return None

        #get <topology>
        if xd_topol_list.has_key(const.XML_TAG_TOPOL):
            topol_list = util.to_array(xd_topol_list[const.XML_TAG_TOPOL])
        else:
            logger.warn('tag <{0}> is not specified.'.format(const.XML_TAG_TOPOL))
            return None

        topol_dict_list = []
        for xd_topol in topol_list:
            topol_dict = dict()
            #get topology type.<topology type=xxx>
            if xd_topol.has_key('@'+const.XML_ATTR_TYPE):
                topol_type = xd_topol['@'+const.XML_ATTR_TYPE].lower()
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_TOPOL,const.XML_ATTR_TYPE))
                return None
            
            if not topol_type == const.TYPE_NW_PHYSICAL and \
                not topol_type == const.TYPE_NW_SLICE:
                logger.warn('attribute <{0} {1}={2}> is invalid value.'\
                            .format(const.XML_TAG_TOPOL,const.XML_ATTR_TYPE,topol_type))
                return None
        
            #get topology last_update_time.<topology last_update_time=xxx>
            if xd_topol.has_key('@'+const.XML_ATTR_LAST_UPD_TIME):
                topol_time = xd_topol['@'+const.XML_ATTR_LAST_UPD_TIME]
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_TOPOL,const.XML_ATTR_LAST_UPD_TIME))
                return None
    
            if xd_topol.has_key('@'+const.XML_ATTR_NAME):
                nw_name = xd_topol['@'+const.XML_ATTR_NAME]
            else:
                logger.warn('attribute <{0} {1}> is not specified.'\
                            .format(const.XML_TAG_NW,const.XML_ATTR_NAME))
                return None

            #In the case of slice topology, to get the status and owner.
            if topol_type == const.TYPE_NW_SLICE:
                #get network status<network status=xxx>
                if xd_topol.has_key('@'+const.XML_ATTR_STS):
                    nw_sts = xd_topol['@'+const.XML_ATTR_STS]

                else:
                    logger.warn('attribute <{0} {1}> is not specified.'\
                                .format(const.XML_TAG_NW,const.XML_ATTR_STS))
                    return None

                #get network owner(=user)<network owner=xxx>
                if xd_topol.has_key('@'+const.XML_ATTR_OWN):
                    nw_own = xd_topol['@'+const.XML_ATTR_OWN]
                else:
                    logger.warn('attribute <{0} {1}> is not specified.'\
                                .format(const.XML_TAG_NW,const.XML_ATTR_OWN))
                    return None

                # slice topology only.
                #add network status and network owner.
                topol_dict[const.XML_ATTR_STS] = nw_sts
                topol_dict[const.XML_ATTR_OWN] = nw_own
    
            # common to physical and slice topology.
            topol_dict[const.XML_ATTR_TYPE] = topol_type
            topol_dict[const.XML_ATTR_LAST_UPD_TIME] = topol_time
            topol_dict[const.XML_ATTR_NAME] = nw_name
    
            #get <node>
            node_dict_list = parse_node_xml(xd_topol)
            if not node_dict_list:
                return None
    
            #add node dictionary list.
            topol_dict[const.XML_TAG_NODE] = node_dict_list
    
            #get <link>
            link_dict_list = parse_link_xml(xd_topol)
            if not link_dict_list:
                link_dict_list = []

            #add link dictionary list.
            topol_dict[const.XML_TAG_LINK] = link_dict_list

            # append topology dict
            topol_dict_list.append(topol_dict)

    except Exception:
        logger.exception('parse_topology_xml')
        return None

    return topol_dict_list

def create_node_xml(xml_topology, network_name):
    #search node in network. 
    node_list = Node.query.filter(Node.network_name == network_name).all()
    for node in node_list:
        #add <node id='xxx' type='xxx'>
        xml_node = SubElement(xml_topology, const.XML_TAG_NODE,
                                {const.XML_ATTR_ID:node.node_name,
                                 const.XML_ATTR_TYPE:node.type
                                    })

### VM on Server is create in the GUI side based on vm_info
#         if node.type == const.TYPE_NODE_SRV:
#             #add <server_info>
#             xml_server_info = SubElement(xml_node, const.XML_TAG_SRV_INFO)
#             #add <vm_id>xxx</vm_id>
#             for vm_mapping in VMMapping.query.filter(VMMapping.idServer == node.id).all():
#                 SubElement(xml_server_info, const.XML_TAG_VM_ID).text \
#                     = vm_mapping.vm_node.node_name
#         
#         elif node.type == const.TYPE_NODE_VM:
        if node.type == const.TYPE_NODE_VM:
            #add <vm_info>
            xml_vm_info = SubElement(xml_node, const.XML_TAG_VM_INFO)
            #add <server_id>xxx</server_id>
            tmp_vm_mapping = VMMapping.query.filter(VMMapping.idVM == node.id).first()
            if tmp_vm_mapping:
                SubElement(xml_vm_info, const.XML_TAG_SRV_ID).text \
                    = tmp_vm_mapping.server_node.node_name
        
        for inter_face in InterFace.query.filter(InterFace.idNode == node.id).all():
            #add <interface id='xxx'>
            xml_if = SubElement(xml_node, const.XML_TAG_IF,
                                 {const.XML_ATTR_ID:inter_face.if_name})
            if inter_face.node.type == const.TYPE_NODE_SW or inter_face.node.type == const.TYPE_NODE_SE:
                #add <port num='xxx'>
                SubElement(xml_if, const.XML_TAG_PORT,
                                 {const.XML_ATTR_NUM:inter_face.port})

    return

def create_link_xml(xml_root, network_name, crrent_link=None):
    if not crrent_link:
        #search link in the network.
        link_list = Link.query.filter(Link.network_name == network_name) \
                                .filter(Link.abst_idLink == None).all()
    else:
        link_list = Link.query.filter(Link.network_name == network_name) \
                                .filter(Link.abst_idLink == crrent_link.id).all()
                                    
    for link in link_list:
        #add <link type=xxx>
        xml_link = SubElement(xml_root, const.XML_TAG_LINK,
                             {const.XML_ATTR_TYPE:link.type})
        if link.link_name:
            xml_link.set(const.XML_ATTR_ID,link.link_name)
     
        srcif_name = '*'
        if link.src_if:
            srcif_name = link.src_if.if_name
        #add (source I/F) <interface_ref client_id='xxx'>
        SubElement(xml_link, const.XML_TAG_IF_REF,
                             {const.XML_ATTR_CLIENT_ID:srcif_name})

        dstif_name = '*'
        if link.dst_if:
            dstif_name = link.dst_if.if_name
        #add (destination I/F) <interface_ref client_id='xxx'>
        SubElement(xml_link, const.XML_TAG_IF_REF,
                             {const.XML_ATTR_CLIENT_ID:dstif_name})
        
        # create abstract link.<link>(Recursively call)
        if link.type == const.TYPE_LINK_ABST_SDN:
            create_link_xml(xml_link,network_name,link)
        
    return

def insert_link(link_list,db_nw,crrent_link=None):
    # sub query.(search node in the network.)
    subq = select().where(Node.network_name == db_nw.network_name).with_only_columns([Node.id])

    for link in link_list:
        ifref_list = link[const.XML_TAG_IF_REF]
        db_srcif_id = None
        db_dstif_id = None

        srcif_name = None
        if not ifref_list[0] == '*':
            srcif_name = ifref_list[0]

        dstif_name = None
        if not ifref_list[1] == '*':
            dstif_name = ifref_list[1]

        link_name = None
        if link.has_key(const.XML_ATTR_ID):
            link_name = link[const.XML_ATTR_ID]

        link_type = None
        if link.has_key(const.XML_ATTR_TYPE):
            link_type = link[const.XML_ATTR_TYPE]

        link_abst_id = None
        if crrent_link:
            link_abst_id = crrent_link.id

        # find a interface in the network.
        db_srcif = None
        if srcif_name:
            db_srcif = InterFace.query.filter(InterFace.idNode.in_(subq))\
                                        .filter(InterFace.if_name == srcif_name).first()
            if not db_srcif:
                logger.warn('Interface({0}) can not be found.'.format(srcif_name))
                continue
            db_srcif_id = db_srcif.id

        # find a interface in the network.
        db_dstif = None
        if dstif_name:
            db_dstif = InterFace.query.filter(InterFace.idNode.in_(subq))\
                                        .filter(InterFace.if_name == dstif_name).first()
            if not db_dstif:
                logger.warn('Interface({0}) can not be found.'.format(dstif_name))
                continue
            db_dstif_id = db_dstif.id
            
        # Existence check.
        db_link = Link.query.filter(Link.src_idIF == db_srcif_id) \
                                .filter(Link.dst_idIF == db_dstif_id) \
                                .filter(Link.type == link_type) \
                                .filter(Link.network_name == db_nw.network_name) \
                                .filter(Link.link_name == link_name) \
                                .filter(Link.abst_idLink == link_abst_id) \
                                .first()
        if db_link:
            logger.debug('link({0}-{1}) is Already existence.'.format(db_link.src_idIF,db_link.dst_idIF))
            continue

        db_link = Link.query.filter(Link.src_idIF == db_dstif_id) \
                                .filter(Link.dst_idIF == db_srcif_id) \
                                .filter(Link.type == link_type) \
                                .filter(Link.network_name == db_nw.network_name) \
                                .filter(Link.link_name == link_name) \
                                .filter(Link.abst_idLink == link_abst_id) \
                                .first()
        if db_link:
            logger.debug('link({0}-{1}) is Already existence.'.format(db_link.src_idIF,db_link.dst_idIF))
            continue

        # insert DB.
        db_link = Link(src_idIF=db_srcif_id,dst_idIF=db_dstif_id
                       ,type=link_type,network_name=db_nw.network_name
                       ,link_name=link_name,abst_idLink=link_abst_id,)
        session.commit()        

        # register the abstract link in the case of (link_type=="sdn").
        if link.has_key(const.XML_TAG_LINK):
            insert_link(link[const.XML_TAG_LINK],db_nw,db_link)

def insert_node(node_list,db_nw,crrent_node=None):
    ### insert node
    for node in node_list:
        # register the VM in the case of (topology_type=="slice" and node_type=="server").
        if db_nw.type == const.TYPE_NW_SLICE and node[const.XML_ATTR_TYPE] == const.TYPE_NODE_SRV:
            db_node = Node.query.filter(Node.type == node[const.XML_ATTR_TYPE]) \
                                    .filter(Node.node_name == node[const.XML_ATTR_ID]).first()
            if not db_node:
                logger.warn('server node({0}) is not existence.(VM can not be registered.)'
                            .format(node[const.XML_ATTR_ID]))
                continue

            if node.has_key(const.XML_TAG_NODE):
                insert_node(node[const.XML_TAG_NODE],db_nw,db_node)
            continue

        # Existence check.
        db_node = Node.query.filter(Node.type == node[const.XML_ATTR_TYPE]) \
                                .filter(Node.node_name == node[const.XML_ATTR_ID])\
                                .filter(Node.network_name == db_nw.network_name).first()
        if db_node:
            logger.debug('node({0}) is Already existence.'.format(db_node.node_name))
        else:
            # insert DB.
            db_node = Node(type=node[const.XML_ATTR_TYPE]
                            ,node_name=node[const.XML_ATTR_ID]
                            ,network_name=db_nw.network_name
                                )
            session.commit()

        ### insert management details
        mgmt = []
        if node.has_key(const.XML_TAG_MGMT):
            mgmt = node[const.XML_TAG_MGMT]
            db_mgmt = NodeManagement.query.filter(NodeManagement.idNode == db_node.id).first()
            if db_mgmt:
                logger.debug('management for node({0}) already exists.'.format(node[const.XML_ATTR_ID]))
                continue
            if not mgmt.has_key(const.XML_ATTR_MGMT_TYPE):
                logger.debug('management for node({0}) has no type.'.format(node[const.XML_ATTR_ID]))
            else:
                mgmt_type = mgmt[const.XML_ATTR_MGMT_TYPE]
                mgmt_address = None
                mgmt_port = None
                mgmt_auth_id = None
                mgmt_auth_pass = None
                if mgmt.has_key(const.XML_TAG_MGMT_ADDRESS):
                    mgmt_address = mgmt[const.XML_TAG_MGMT_ADDRESS]
                if mgmt.has_key(const.XML_TAG_MGMT_PORT):
                    mgmt_port = mgmt[const.XML_TAG_MGMT_PORT]
                if mgmt.has_key(const.XML_TAG_MGMT_AUTH_ID):
                    mgmt_auth_id = mgmt[const.XML_TAG_MGMT_AUTH_ID]
                if mgmt.has_key(const.XML_TAG_MGMT_AUTH_PASS):
                    mgmt_auth_pass = mgmt[const.XML_TAG_MGMT_AUTH_PASS]
            
                db_mgmt = NodeManagement(idNode=db_node.id
                                   ,type=mgmt_type
                                   ,address=mgmt_address
                                   ,port=mgmt_port
                                   ,auth_id=mgmt_auth_id
                                   ,auth_pass=mgmt_auth_pass )
                session.commit()

        ### insert interface
        if_list = []
        if node.has_key(const.XML_TAG_IF):
            if_list = node[const.XML_TAG_IF]
        for interface in if_list:
            # Existence check.
            db_if = InterFace.query.filter(InterFace.idNode == db_node.id) \
                                    .filter(InterFace.if_name == interface[const.XML_ATTR_ID]).first()
            if db_if:
                logger.debug('interface({0}) already exists.'.format(db_if.if_name))
                continue

            port_num = None
            if interface.has_key(const.XML_TAG_PORT):
                port_num = interface[const.XML_TAG_PORT]

            # insert DB.
            db_if = InterFace(idNode=db_node.id
                            ,if_name=interface[const.XML_ATTR_ID]
                            ,port=port_num
                                )
            session.commit()        

        ### insert vm-mapping
        if db_node.type == const.TYPE_NODE_VM:
            # Existence check.
            db_vmmap = VMMapping.query.filter(VMMapping.idServer == crrent_node.id) \
                                    .filter(VMMapping.idVM == db_node.id).first()
            if db_vmmap:
                logger.debug('interface({0}-{1}) is Already existence.'.format(db_vmmap.idServer,db_vmmap.idVM))
            else:
                # insert DB.
                db_vmmap = VMMapping(idServer=crrent_node.id,idVM=db_node.id)
                session.commit()        

    return

def insert_topol(topol_dict):
    logger.debug('insert topology -start-')
    try:
        # lock -start-
        with util.semaphore_tpl:
            with util.semaphore_md:
                #open DB connection.
                tpldb_setup()
                
                ### insert topology
                # Existence check.
                db_nw = Network.query.filter(Network.type == topol_dict[const.XML_ATTR_TYPE]) \
                                        .filter(Network.network_name == topol_dict[const.XML_ATTR_NAME]).first()
                if db_nw:
                    logger.debug('network({0}) is Already existence.'.format(db_nw.network_name))
                    # update DB.
                    db_nw.last_update_time=topol_dict[const.XML_ATTR_LAST_UPD_TIME]
                    session.commit()
        
                else:
                    nw_owner = None
                    if topol_dict[const.XML_ATTR_TYPE] == const.TYPE_NW_SLICE:
                        if topol_dict.has_key(const.XML_ATTR_OWN):
                            nw_owner = topol_dict[const.XML_ATTR_OWN]
        
                    #get now time.(UTC:0)
                    now_time = calendar.timegm(datetime.utcnow().timetuple())
            
                    # insert DB.
                    db_nw = Network(type=topol_dict[const.XML_ATTR_TYPE]
                                    ,registration_time=now_time
                                    ,last_update_time=topol_dict[const.XML_ATTR_LAST_UPD_TIME]
                                    ,network_name=topol_dict[const.XML_ATTR_NAME]
                                    ,user=nw_owner
                                        )
                    session.commit()
        
                ### insert node
                node_list = []
                if topol_dict.has_key(const.XML_TAG_NODE):
                    node_list = topol_dict[const.XML_TAG_NODE]
        
                insert_node(node_list,db_nw)
        
                ### insert link
                link_list = []
                if topol_dict.has_key(const.XML_TAG_LINK):
                    link_list = topol_dict[const.XML_TAG_LINK]
        
                insert_link(link_list,db_nw)
        # lock -end-

    except Exception:
        logger.exception('insert topology error.')
        raise

    finally:
        #close topology database connection.
        tpldb_close()
        logger.debug('insert topology -end-')

    return

def del_md(nw_name,regist_time,mon_data_db):
    logger.debug('delete monitoring-data -start-')
    #database handle.
    db_handle = DBHandle()
    try:
        #get now time.(UTC:0)
        now_time = calendar.timegm(datetime.utcnow().timetuple())
    
        # search target table name.
        # time-range=registration_time-now_time.
        if not regist_time :
            logger.warn('Target network can not be found.')
            return

        db_con = None
        try:
            #connect to the database.
            db_con = db_handle.connect(mon_data_db,config.db_addr
                                       ,config.db_port,config.db_user,config.db_pass)
        except Exception:
            # It is not an error.
            logger.debug('{0} is unknown database.'.format(mon_data_db))
            return

        #search target table name.
        tbl_name_list = search_target_table(logger,int(regist_time),int(now_time),mon_data_db)

        #no data in the search time-range.
        if not tbl_name_list:
            logger.debug('no data in the search time-range.({0}-{1})'.format(regist_time,now_time))
            return

        # search database.(metaID)
        sql = "SELECT metaID FROM metaData WHERE network_name='{0}'".format(nw_name)
        logger.debug(sql)
        db_con.execute(sql)
         
        res_metaid_list = db_con.fetchall()
        sql_where_list = []
        for res_metaid in res_metaid_list:
            sql_where = " metaID={0} ".format(res_metaid['metaID'])
            sql_where_list.append(sql_where)

        if not sql_where_list:
            # no metaData.
            return

        # delete database.(data)
        sql_where = " OR ".join(sql_where_list)
        for tbl_name in tbl_name_list:
            sql = "DELETE FROM {0} WHERE {1}".format(tbl_name,sql_where)
            logger.debug(sql)
            db_con.execute(sql)

        # delete database.(metaData)
        sql = "DELETE FROM metaData WHERE network_name='{0}'".format(nw_name)
        logger.debug(sql)
        db_con.execute(sql)

        # delete commit.(monitoring-data and metaData)
        db_handle.commit()

    except Exception:
        logger.exception('delete monitoring-data error.')
        raise

    finally:
        #close monitoring database connection.
        db_handle.close()
        logger.debug('delete monitoring-data -end-')

    return

def del_topol(topol_dict,md_flg=False):
    logger.debug('delete topology -start-')
    try:
        # lock -start-
        with util.semaphore_tpl:
            with util.semaphore_md:
                #open DB connection.
                tpldb_setup()
                
                #get all link in topology.
                for link in Link.query.filter(Link.network_name == topol_dict[const.XML_ATTR_NAME]).all():
                    ### delete link
                    link.delete()

                #get all node in topology.
                for node in Node.query.filter(Node.network_name == topol_dict[const.XML_ATTR_NAME]).all():
                    #get all management details in node (should be only one)
                    for mgmt in NodeManagement.query.filter(NodeManagement.idNode == node.id).all():
                        ### delete management details
                        mgmt.delete()

                    #get all interface in node.
                    for interface in InterFace.query.filter(InterFace.idNode == node.id).all():       
                        ### delete interface
                        interface.delete()
        
                    #get all of the vm-mappings that node is involved.
                    for vmmap in VMMapping.query.filter((VMMapping.idServer == node.id) | (VMMapping.idVM == node.id)).all():
                        ### delete vm-mapping
                        vmmap.delete()
        
                    ### delete node
                    node.delete()
        
                # keep in order to remove the monitoring-data.
                nw_name = None
                regist_time = None
                nw = Network.query.filter(Network.network_name == topol_dict[const.XML_ATTR_NAME]).first()
                if nw:
                    nw_name = nw.network_name
                    regist_time = nw.registration_time
                    ### delete network
                    nw.delete()
        
                session.commit()
        # lock -end-

        ### delete monitoring-data
        if md_flg is True:
            # delete monitoring-data-sdn
            del_md(nw_name,regist_time,config.mon_data_sdn_db)

            # delete monitoring-data-cp
            del_md(nw_name,regist_time,config.mon_data_cp_db)

            # delete monitoring-data-se
            del_md(nw_name,regist_time,config.mon_data_se_db)

            # delete monitoring-data-tn
            del_md(nw_name,regist_time,config.mon_data_tn_db)

    except Exception:
        logger.exception('delete topology error.')
        raise

    finally:
        #close topology database connection.
        tpldb_close()
        logger.debug('delete topology -end-')

    return

@route(BASE_URI, method='GET')
@route(BASE_URI + '/', method='GET')
def topology_list():
    logger.info('GET topology list. -start-')
    try:
        # lock -start-
        with util.semaphore_tpl:
            #open DB connection.
            tpldb_setup()
    
            #create <topology_list>
            xml_topology_list = Element(const.XML_TAG_TOPOL_LIST)
            
            nw_list = Network.query.all()
            for nw in nw_list:
                #add <topology type='slice' last_update_time='xxx' name='xxx' owner='xxx'>
                xml_topology = SubElement(xml_topology_list, const.XML_TAG_TOPOL,
                                            {const.XML_ATTR_TYPE:nw.type,
                                             const.XML_ATTR_LAST_UPD_TIME:str(nw.last_update_time),
                                             const.XML_ATTR_NAME:nw.network_name
                                                })
    
                if nw.type == const.TYPE_NW_SLICE:
                    xml_topology.set(const.XML_ATTR_OWN,nw.user)
        # lock -end-

    except Exception:
        logger.exception('GET topology list error.')
        return HTTPResponse("GET topology list error.", status=500)

    finally:
        #close DB connection.
        tpldb_close()
    logger.info('GET topology list. -end-')

    return util.prettify(xml_topology_list)

@route(BASE_URI + '/' + const.TYPE_NW_PHYSICAL, method='GET')
@route(BASE_URI + '/'+ const.TYPE_NW_PHYSICAL +'/', method='GET')
def physical_topology_get():
    logger.info('GET {0} topology. -start-'.format(const.TYPE_NW_PHYSICAL))
    try:
        # lock -start-
        with util.semaphore_tpl:
            #open DB connection.
            tpldb_setup()
    
            #create <topology_list>
            xml_topology_list = Element(const.XML_TAG_TOPOL_LIST)
            
            nw_list = Network.query.filter(Network.type == const.TYPE_NW_PHYSICAL).all()        
            for nw in nw_list:
                #add <topology type='slice' last_update_time='xxx' name='xxx' owner='xxx'>
                xml_topology = SubElement(xml_topology_list, const.XML_TAG_TOPOL,
                                            {const.XML_ATTR_TYPE:nw.type,
                                             const.XML_ATTR_LAST_UPD_TIME:str(nw.last_update_time),
                                             const.XML_ATTR_NAME:nw.network_name
                                                })
    
                #create node xml
                create_node_xml(xml_topology, nw.network_name)
                #create link xml
                create_link_xml(xml_topology, nw.network_name)
        # lock -end-

    except Exception:
        logger.exception('GET physical topology error.')
        return HTTPResponse("GET physical topology error.", status=500)

    finally:
        #close DB connection.
        tpldb_close()
    logger.info('GET {0} topology. -end-'.format(const.TYPE_NW_PHYSICAL))

    return util.prettify(xml_topology_list)

@route(BASE_URI + '/'+ const.TYPE_NW_SLICE +'/<slice_id>', method='GET')
def slice_topology_get( slice_id="default_slice_id" ):
    logger.info('GET {0} topology.(slice_id={1})'.format(const.TYPE_NW_SLICE,slice_id))
    try:
        # lock -start-
        with util.semaphore_tpl:
            #open DB connection.
            tpldb_setup()
    
            #create <topology_list>
            xml_topology_list = Element(const.XML_TAG_TOPOL_LIST)
                
            #add <network type='slice' last_update_time='xxx'>
            nw = Network.query.filter(Network.type == const.TYPE_NW_SLICE)\
                                .filter(Network.network_name == slice_id).first()
            if not nw:
                return util.prettify(xml_topology_list)
    
            #add <topology type='slice' last_update_time='xxx' name='xxx' owner='xxx'>
            xml_topology = SubElement(xml_topology_list, const.XML_TAG_TOPOL,
                                        {const.XML_ATTR_TYPE:nw.type,
                                         const.XML_ATTR_LAST_UPD_TIME:str(nw.last_update_time),
                                         const.XML_ATTR_NAME:nw.network_name
                                            })
    
            #create node xml
            create_node_xml(xml_topology, slice_id)
            #create link xml
            create_link_xml(xml_topology, slice_id)
        # lock -end-
    
    except Exception:
        logger.exception('GET slice topology error.')
        return HTTPResponse("GET slice topology error.", status=500)

    finally:
        #close DB connection.
        tpldb_close()

    return util.prettify(xml_topology_list)

@route(BASE_URI, method='POST')
@route(BASE_URI + '/', method='POST')
def topology_post():
    logger.info('POST topology. -start-')
    try:
        #get request body.(xml message.)
        param_list=request.body
        param_string=""
        for row in param_list:
            param_string += row
        if not param_string:
            logger.warn('no message.')
            return HTTPResponse("POST topology error.(request body is empty.)", status=400)

        # parse xml to dictionary.
        topol_dict_list = parse_topology_xml(param_string)
        if not topol_dict_list:
            logger.warn('parse topology xml error.')
            return HTTPResponse("POST topology error.(parse topology xml error.)", status=400)
        logger.debug(topol_dict_list) 
        
        for topol_dict in topol_dict_list:
            # topology to DB.
            if topol_dict[const.XML_ATTR_TYPE] == const.TYPE_NW_PHYSICAL:
                logger.debug('topology add.(type={0})'.format(const.TYPE_NW_PHYSICAL))
                # physical topology will be inserted after you delete all the information of the domain of interest.
                # delete from DB.(monitoring-data is not deleted.)
                del_topol(topol_dict)
     
                # insert DB.
                insert_topol(topol_dict)
     
            elif topol_dict[const.XML_ATTR_TYPE] == const.TYPE_NW_SLICE:
                logger.debug('topology add.(type={0},status={1})'.format(const.TYPE_NW_SLICE,topol_dict[const.XML_ATTR_STS]))
                # status == Provision is insert DB.(start monitoring)
                # status == Delete is delete DB.(stop monitoring)
                # ignore　other status.
                if topol_dict[const.XML_ATTR_STS] == const.SLICE_STS_PROV:
                    # insert DB.
                    insert_topol(topol_dict)
     
                elif topol_dict[const.XML_ATTR_STS] == const.SLICE_STS_DEL:
                    # delete from DB.(Delete monitoring-data also together.)
                    del_topol(topol_dict,True)

                else :
                    # ignore other status.
                    logger.debug('slice-status to ignore except "{0}" or "{1}"(status={2}).'\
                                .format(const.SLICE_STS_PROV,const.XML_ATTR_STS,topol_dict[const.XML_ATTR_STS]))
                
    except Exception:
        logger.exception('POST topology error.')
        return HTTPResponse("POST topology error.", status=500)
    logger.info('POST topology. -end-')

    return
