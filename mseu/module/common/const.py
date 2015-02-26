#!/usr/bin/env python
# -*- coding: UTF-8 -*-

### constants
# utillity
SYSTEM_NAME             = 'monitoring-system'
MODULE_NAME_API         = 'monitoring_api'
MODULE_NAME_COL         = 'monitoring_data_collector'
SEC_ONEDAY              = 86400
HTTP_TIME_OUT           = 10

# REST
REST_MONITORING         = 'monitoring'
REST_TOPOL              = 'topology'

# type
TYPE_NW_PHYSICAL        = 'physical'
TYPE_NW_SLICE           = 'slice'
TYPE_NODE_SW            = 'switch'
TYPE_NODE_SRV           = 'server'
TYPE_NODE_VM            = 'vm'
TYPE_LINK_LAN           = 'lan'
TYPE_LINK_TN            = 'tn'
TYPE_MON_SDN            = 'network_sdn'
TYPE_MON_TN             = 'network_tn'
TYPE_MON_CP             = 'cp'
TYPE_AGG_AVG            = '0'
TYPE_AGG_LAST           = '1'
TYPE_TS_REP             = '0'
TYPE_TS_NREP            = '1'
TYPE_MGMT_SNMP          = 'snmp'

# slice status
SLICE_STS_PROV = 'geni_provisioned'
SLICE_STS_DEL  = 'geni_unallocated'

# xml tag
XML_TAG_TOPOL_LIST      = 'topology_list'
XML_TAG_TOPOL           = 'topology'
XML_TAG_NW              = 'network'
XML_TAG_NODE            = 'node'
XML_TAG_SRV_INFO        = 'server_info'
XML_TAG_VM_ID           = 'vm_id'
XML_TAG_VM_INFO         = 'vm_info'
XML_TAG_SRV_ID          = 'server_id'
XML_TAG_IF              = 'interface'
XML_TAG_PORT            = 'port'
XML_TAG_LINK            = 'link'
XML_TAG_IF_REF          = 'interface_ref'
XML_TAG_MON_DATA        = 'monitoring-data'
XML_TAG_PARAM           = 'parameter'
XML_TAG_VAL             = 'value'
XML_TAG_MGMT            = 'management'
XML_TAG_MGMT_ADDRESS    = 'address'
XML_TAG_MGMT_PORT       = 'port'
XML_TAG_MGMT_AUTH       = 'auth'
XML_TAG_MGMT_TYPE       = 'type'

# xml attribute
XML_ATTR_TYPE           = 'type'
XML_ATTR_LAST_UPD_TIME  = 'last_update_time'
XML_ATTR_NAME           = 'name'
XML_ATTR_STS            = 'status'
XML_ATTR_OWN            = 'owner'
XML_ATTR_ID             = 'id'
XML_ATTR_NUM            = 'num'
XML_ATTR_CLIENT_ID      = 'client_id'
XML_ATTR_FWD            = 'forward'
XML_ATTR_TIME_STAMP     = 'timestamp'
XML_ATTR_MGMT_TYPE      = 'type'

# HTTP GET option.
HTTP_GET_OPT_TYPE        = 'type'
HTTP_GET_OPT_TOPOL       = 'topology'
HTTP_GET_OPT_NODE        = 'node'
HTTP_GET_OPT_PORT        = 'port'
HTTP_GET_OPT_STIME       = 'time-start'
HTTP_GET_OPT_ETIME       = 'time-end'
HTTP_GET_OPT_LMT         = 'limit'

# database
DEFAULT_LIMIT            = 10
DB_COL_META_ID           = 'metaID'
DB_COL_NW_NAME           = 'network_name'
DB_COL_NODE_NAME         = 'node_name'
DB_COL_PORT              = 'port'
DB_COL_TYPE              = 'type'
DB_COL_TIME_STAMP        = 'timestamp'
DB_COL_VAL               = 'value'

# zabbix
ZBX_SRV_STS              = 'felix.host.status'
ZBX_VM_STS               = 'felix.uservm.status'

