Monitoring Prototype
====================

Prerequisites
-------------

User:
Any (e.g. `mon_user` with administrator privileges, or root, etc)

Install directory:
Any (e.g. `/home/mon_user`)

GIT repository:
ANy (e.g. `/opt/felix`)


Installing
----------

1. Install module
  * $ cp -r /opt/felix/msjp /home/mon_user/

1. Install library
  * $ sudo aptitude install -y python apache2 mysql-server python-mysqldb python-elixir curl python-pip  python-bottle
    * # python-bottle needs SQLAlchemy==0.7.8 (e.g. pip install SQLAlchemy==0.7.8 or apt-get install python-sqlalchemy==0.7.8-1)
  * $ sudo pip install xmltodict
  * $ sudo pip install requests
  * $ sudo pip install pyzabbix
  * $ sudo pip install gevent
  * $ sudo pip install "python-dateutil==1.5"
  * $ sudo easy_install apscheduler
 
1. Create database.
  * $ mysql -u root < /home/mon_user/msjp/schema/monTopologyDB.sql
  * $ mysql -u root < /home/mon_user/msjp/schema/monDataSDNDB.sql
  * $ mysql -u root < /home/mon_user/msjp/schema/monDataCPDB.sql
  * $ mysql -u root < /home/mon_user/msjp/schema/monDataSEDB.sql
  * $ mysql -u root < /home/mon_user/msjp/schema/monDataTNDB.sql


Configuring
-----------

Configuration file: `/home/mon_user/msjp/conf/mon_api.conf`

```
[REST]
rest_host=0.0.0.0
rest_port=8449

[URI]
#master-monitoring-server[EU] URI
post_uri=http://xxx.xxx.xxx.xxx:8449/monitoring-system/monitoring

[DATABASE]
db_addr=127.0.0.1
db_port=3306
db_user=root
db_pass=<fill_with_yours>

[UTILITY]
#debug=0
debug=1
```

Configuration file: `/home/mon_user/msjp/conf/mon_col.conf`

```
[URI]
#master-monitoring-server URI
post_uri=http://127.0.0.1:8449/monitoring-system/monitoring
sequel_service_uri=http://127.0.0.1:8015/perfSONAR_PS/services/sequel
nsi_uri=http://127.0.0.1/tn_monitoring_data.xml

[DATABASE]
db_addr=127.0.0.1
db_port=3306
db_user=root
db_pass=<fill_with_yours>

[ZABBIX]
zabbix_uri=http://127.0.0.1/zabbix
zabbix_user=Admin
zabbix_pass=zabbix

[MONITORING]
#[monitoring-class name(full path),interval(sec)],[...]...
#e.g. [module.collector.sdn.MonitoringDataSDN,60]
monitoring_module=["module.collector.ps.sdn.MonitoringDataSDN",10],["module.collector.zabbix.cp.MonitoringDataCP",10],["module.collector.ps.se.MonitoringDataSE",10]
#monitoring_module=["module.collector.nsi.tn.MonitoringDataTN",3]

#[monitoring-data-name,aggregate-type(0=Average value,1=Last value)],[...]...
#e.g. ["status",1],["in_bps",0],["out_bps",0]
ps_sdn_monitoring_item=["status",1],["in_bps",0],["out_bps",0]
ps_se_monitoring_item=["status",1],["in_bps",0],["out_bps",0]

#[monitoring-data-name,zabbix-item-name,timestamp-type(0=not replace,1=replace)],[...]...
#e.g. ["cpu_load","system.cpu.load",0]
zabbix_cp_monitoring_item_server=["cpu_load","system.cpu.load",0]
zabbix_cp_monitoring_item_vm=["cpu_load","felix.uservm.load",0]

[UTILITY]
#Whether the monitoring data to Aggregate.(0=not aggreagete,1=to aggregate)
#aggregate=0
aggregate=1

#debug mode.(0=off,1=on)
debug=0
#debug=1
```

Running
-------

[Monitoring API]
`$ cd /home/mon_user/msjp/bin`

Running:
`$ ./monitoring_api start`

Stopping:
`$ ./monitoring_api stop`

Log file:
`$ tail -f /home/mon_user/msjp/log/monitoring_api.log`

[Monitoring data collector]
`$ cd /home/mon_user/msjp/bin`

Running:
`$ ./monitoring_data_collector start`

Stopping:
`$ ./monitoring_data_collector stop`

Log file:
`$ tail -f /home/mon_user/msjp/log/monitoring_data_collector.log`

How to use
----------

'''POST topology'''

`$ curl -X POST -d @post_topology_physical.xml http://127.0.0.1:8449/monitoring-system/topology`

e.g.
`$ cat post_topology_physical.xml`
```
<topology_list>
  <topology last_update_time="1412670730" type="physical" name="urn:publicid:IDN+ocf:i2cat">

    <!-- server id == node id -->
    <node id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer" type="server">
      <management type="vm">
        <auth_user/>
        <auth_password/>
      </management>
      <!-- interface id == interface id -->
      <interface id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
    </node>

    <!-- switch id == node_id -->
    <node id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02" type="switch">
      <management type="snmp">
        <snmp_addr>192.168.1.1</snmp_addr>
        <snmp_port>161</snmp_port>
        <snmp_community>public</snmp_community>
      </management>
      <!-- interface_id == interface id -->
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12">
          <!-- port number == port num -->
          <port num="12"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10">
          <!-- port number == port num -->
          <port num="10"/>
      </interface>
    </node>

    <!-- Server: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12"/>
    </link>
  </topology>

  <topology last_update_time="1412670731" type="physical" name="urn:publicid:IDN+ocf:jgnx">
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6">
          <port num="6"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13">
          <port num="13"/>
      </interface>
    </node>
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server1" type="server">
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server1+eth1"/>
    </node>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:jgnx:vtam:server1+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13"/>
    </link>
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11">
          <port num="11"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1">
          <port num="1"/>
      </interface>
    </node>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11"/>
    </link>
  </topology>
</topology_list>
```

'''GET topology'''
`$ curl -X GET http://127.0.0.1:8080/monitoring-system/topology/physical`

e.g. response topology xml
```
<?xml version="1.0" ?>
<topology_list>
  <topology last_update_time="1412670730" name="urn:publicid:IDN+ocf:i2cat" type="physical">
    <node id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer" type="server">
      <server_info/>
      <interface id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
    </node>
    <node id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12">
        <port num="12"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10">
        <port num="10"/>
      </interface>
    </node>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12"/>
    </link>
  </topology>
  <topology last_update_time="1412670731" name="urn:publicid:IDN+ocf:jgnx" type="physical">
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6">
        <port num="6"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13">
        <port num="13"/>
      </interface>
    </node>
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server1" type="server">
      <server_info/>
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server1+eth1"/>
    </node>
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11">
        <port num="11"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1">
        <port num="1"/>
      </interface>
    </node>
  </topology>
</topology_list>
```
