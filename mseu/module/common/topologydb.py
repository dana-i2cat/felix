#!/usr/bin/env python
# -*- coding: UTF-8 -*-
 
import module.common.const as const
from sqlalchemy.orm import join
from elixir import *

class Network(Entity):
    using_options(tablename='M_NETWORK', autoload=True)

class Node(Entity):
    using_options(tablename='M_NODE', autoload=True)
    network = ManyToOne('Network',primaryjoin=lambda: Node.network_name == Network.network_name,
                               foreign_keys=lambda: [Node.network_name])

class NodeInfo(Entity):
    using_options(tablename='M_NODE_INFO', autoload=True)
    node = ManyToOne('Node',primaryjoin=lambda: NodeInfo.idNode == Node.id,
                               foreign_keys=lambda: [NodeInfo.idNode])

class NodeManagement(Entity):
    using_options(tablename='M_NODE_MGMT', autoload=True)
    node = ManyToOne('Node',primaryjoin=lambda: NodeManagement.idNode == Node.id,
                               foreign_keys=lambda: [NodeManagement.idNode])

class VMMapping(Entity):
    using_options(tablename='M_VM_MAPPING', autoload=True)
    server_node = ManyToOne('Node',primaryjoin=lambda: VMMapping.idServer == Node.id,
                               foreign_keys=lambda: [VMMapping.idServer])
    vm_node = ManyToOne('Node',primaryjoin=lambda: VMMapping.idVM == Node.id,
                               foreign_keys=lambda: [VMMapping.idVM])

class InterFace(Entity):
    using_options(tablename='M_IF', autoload=True)
    node = ManyToOne('Node',primaryjoin=lambda: InterFace.idNode == Node.id,
                               foreign_keys=lambda: [InterFace.idNode])

class InterFaceInfo(Entity):
    using_options(tablename='M_IF_INFO', autoload=True)
    inter_face = ManyToOne('InterFace',primaryjoin=lambda: InterFaceInfo.idIF == InterFace.id,
                               foreign_keys=lambda: [InterFaceInfo.idIF])

class Link(Entity):
    using_options(tablename='M_LINK', autoload=True)
    src_if = ManyToOne('InterFace',primaryjoin=lambda: Link.src_idIF == InterFace.id,
                               foreign_keys=lambda: [Link.src_idIF])
    dst_if = ManyToOne('InterFace',primaryjoin=lambda: Link.dst_idIF == InterFace.id,
                               foreign_keys=lambda: [Link.dst_idIF])

class LinkInfo(Entity):
    using_options(tablename='M_LINK_INFO', autoload=True)
    link = ManyToOne('Link',primaryjoin=lambda: LinkInfo.idLink == Link.id,
                               foreign_keys=lambda: [LinkInfo.idLink])

def get_all_network(nw_type):
    return Network.query.filter(Network.type == nw_type).all()

def get_all_node(nw=None):
    if nw is None:
        return Node.query.all()
    else:
        return Node.query.filter(Node.network_name == nw.network_name).all()

def get_all_sw(nw=None):
    if nw is None:
        return Node.query.filter(Node.type == const.TYPE_NODE_SW).all()
    else:
        return Node.query.filter(Node.network_name == nw.network_name)\
                            .filter(Node.type == const.TYPE_NODE_SW).all()

def get_all_srv(nw=None):
    if nw is None:
        return Node.query.filter(Node.type == const.TYPE_NODE_SRV).all()
    else:
        return Node.query.filter(Node.network_name == nw.network_name)\
                            .filter(Node.type == const.TYPE_NODE_SRV).all()

def get_all_vm(nw=None):
    if nw is None:
        return Node.query.filter(Node.type == const.TYPE_NODE_VM).all()
    else:
        return Node.query.filter(Node.network_name == nw.network_name)\
                            .filter(Node.type == const.TYPE_NODE_VM).all()

def get_all_mgmt(node):
    return NodeManagement.query.filter(NodeManagement.idNode == node.id).all()

def get_all_if(node):
    return InterFace.query.filter(InterFace.idNode == node.id).all()

def get_all_target_if(node_name,port):
    # search node
    subq = join(InterFace, Node, InterFace.idNode == Node.id) \
            .select(Node.node_name == node_name)

    # To specify the column to get.
    subq =  subq.with_only_columns([InterFace.id])
 
    # look for the interface that node_name and port_num matches.
    return InterFace.query.filter(InterFace.port == port).filter(InterFace.id.in_(subq)).all()

def get_all_sw_if():
    return InterFace.query.filter(InterFace.port != None).all()

def create_metadata(db_name,db_addr,db_port,db_user,db_pass,debug_flg):
    metadata.bind = 'mysql://{0}:{1}@{2}:{3}/{4}'.format(db_user,db_pass,db_addr,str(db_port),db_name)

    if debug_flg == 1:
        metadata.bind.echo = True
    else :
        metadata.bind.echo = False
        
def tpldb_setup():
    setup_all()

def tpldb_close():
    session.close()

def tpldb_exec_sql(sql):
    conn = metadata.bind.engine.connect()
    return conn.execute(sql)
