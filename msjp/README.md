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
  * $ sudo aptitude -y install python apache2 python-mysqldb python-elixir curl python-pip  python-bottle
  * # python-bottle needs SQLAlchemy==0.7.8 (e.g. pip install SQLAlchemy==0.7.8 or apt-get install python-sqlalchemy==0.7.8-1)
  * $ sudo pip install xmltodict
  * $ sudo pip install requests
  * $ sudo pip install pyzabbix
  * $ sudo pip install gevent
  * $ sudo pip install "python-dateutil==1.5"
  * $ sudo easy_install apscheduler
 
1. Create database.
  * cd /home/mon_user/msjp/schema
  * ./create_db.sh

Configuring
-----------

[Monitoring API]
Configuration file: `/home/mon_user/msjp/conf/mon_api.conf`

```
[REST]
# Information for listen on REST-API.
rest_host=0.0.0.0
rest_port=8448

[URI]
# MMS:Other master-monitoring-server URI.
# MS :setting unnecessary.
post_uri=http://xxx.xxx.xxx.xxx:8449/monitoring-system/monitoring

[DATABASE]
# Database access information.
db_addr=127.0.0.1
db_port=3306
db_user=root
db_pass=<fill_with_yours>
```

[Monitoring data collector]
Configuration file: `/home/mon_user/msjp/conf/mon_col.conf`

```
[URI]
# MMS:setting unnecessary.
# MS :master-monitoring-server URI.
post_uri=http://xxx.xxx.xxx.xxx:8448/monitoring-system/monitoring

# MMS:setting unnecessary.
# MS :sequel_service URI.
sequel_service_uri=http://127.0.0.1:8015/perfSONAR_PS/services/sequel

# MMS:NSI(tnrm) URI.
# MS :setting unnecessary.
nsi_uri=http://xxx.xxx.xxx.xxx/tn_monitoring_data.xml

[DATABASE]
# Database access information.
db_addr=127.0.0.1
db_port=3306
db_user=root
db_pass=<fill_with_yours>

[ZABBIX]
# MMS:setting unnecessary.
# MS :ZABBIX access information.
zabbix_uri=http://xxx.xxx.xxx.xxx/zabbix
zabbix_user=Admin
zabbix_pass=zabbix

[MONITORING]
#[monitoring-class name(full path),interval(sec)],[...]...
# MMS:tn-monitoring only.
#monitoring_module=["module.collector.nsi.tn.MonitoringDataTN",10]
# MS:sdn-monitoring and se-monitoring and cp-monitoring.
monitoring_module=["module.collector.ps.sdn.MonitoringDataSDN",10],["module.collector.zabbix.cp.MonitoringDataCP",10],["module.collector.ps.se.MonitoringDataSE",10]

#[monitoring-data-name,aggregate-type(0=Average value,1=Last value)],[...]...
# MMS:setting unnecessary.
# MS :sdn-monitoring item information.
ps_sdn_monitoring_item=["status",1],["in_bps",0],["out_bps",0]

#[monitoring-data-name,aggregate-type(0=Average value,1=Last value)],[...]...
# MMS:setting unnecessary.
# MS :se-monitoring item information.
ps_se_monitoring_item=["status",1],["in_bps",0],["out_bps",0]

#[monitoring-data-name,zabbix-item-name,timestamp-type(0=not replace,1=replace)],[...]...
# MMS:setting unnecessary.
# MS :cp-monitoring item information for server.
zabbix_cp_monitoring_item_server=["cpu_load","system.cpu.load[percpu,avg1]",0]

#[monitoring-data-name,zabbix-item-name,timestamp-type(0=not replace,1=replace)],[...]...
# MMS:setting unnecessary.
# MS :cp-monitoring item information for vm.
zabbix_cp_monitoring_item_vm=["cpu_load","felix.uservm.load",0]

[UTILITY]
#Whether the monitoring data to Aggregate.(0=not aggreagete,1=to aggregate)
#aggregate=0
aggregate=1
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

`$ curl -X POST -d @post_topology_physical.xml http://127.0.0.1:8448/monitoring-system/topology`

e.g.
`$ cat post_topology_physical.xml`
```
<topology_list>
  <!-- domain id == topology name -->
  <topology last_update_time="1412670730" type="physical" name="urn:publicid:IDN+ocf:i2cat">
    <!-- server id == node id -->
    <node id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer" type="server">
      <management type="snmp">
        <address>192.168.2.1</address>
        <port>161</port>
        <auth_id>monitoring</auth_id>
        <auth_pass>felix_monitoring</auth_pass>
      </management>
      <!-- interface id == interface id -->
      <interface id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
    </node>
    <!-- switch id == node_id -->
    <node id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02" type="switch">
      <management type="snmp">
        <address>192.168.1.2</address>
        <port>161</port>
        <auth_id>monitoring</auth_id>
        <auth_pass>felix_monitoring</auth_pass>
      </management>
      <!-- interface id == interface id -->
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12">
          <!-- port number == port num -->
          <port num="12"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10">
          <!-- port number == port num -->
          <port num="10"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_11">
          <!-- port number == port num -->
          <port num="11"/>
      </interface>
    </node>
    <!-- Server: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12"/>
    </link>
    <!-- se_id == node_id -->
    <node id="urn:publicid:i2cat-se1" type="se">
      <management type="snmp">
        <address>192.168.1.2</address>
        <port>161</port>
        <auth_id>monitoring</auth_id>
        <auth_pass>felix_monitoring</auth_pass>
      </management>
      <interface id="urn:publicid:i2cat-se1:if1">
          <!-- port number(interface name?) == port num -->
          <port num="eth1"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if2">
          <port num="eth2"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if3">
          <port num="eth3"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if4">
          <port num="eth4"/>
      </interface>
    </node>
    <!-- SE: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:i2cat-se1:if1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:i2cat-se1:if2"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_11"/>
    </link>
    <!-- tn id == node_id -->
    <node id="urn:publicid:tn-network1" type="tn">
      <interface id="urn:publicid:tn-network1+urn:felix:i2cat-stp1"/>
      <interface id="urn:publicid:tn-network1+urn:felix:i2cat-stp2"/>
    </node>
    <!-- TN: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:i2cat-stp1"/>
      <interface_ref client_id="urn:publicid:i2cat-se1:if3"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:i2cat-stp2"/>
      <interface_ref client_id="urn:publicid:i2cat-se1:if4"/>
    </link>
  </topology>
  <topology last_update_time="1412670731" type="physical" name="urn:publicid:IDN+ocf:jgnx">
    <!-- switch id == node_id -->
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01" type="switch">
      <!-- interface_id == interface id -->
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6">
          <port num="6"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13">
          <port num="13"/>
      </interface>
    </node>
    <!-- switch id == node_id -->
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11">
          <port num="11"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1">
          <port num="1"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_15">
          <port num="15"/>
      </interface>
    </node>
    <!-- server id == node id -->
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server1" type="server">
      <!-- interface id == interface id -->
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server1+interface+eth1"/>
    </node>
    <!-- server id == node id -->
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server2" type="server">
      <!-- interface id == interface id -->
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server2+interface+eth2"/>
    </node>
    <!-- Switch: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1"/>
    </link>
    <!-- Server: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <!-- interface_id == interface id -->
      <interface_ref client_id="urn:publicid:IDN+ocf:jgnx:vtam:server1+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:jgnx:vtam:server2+interface+eth2"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_15"/>
    </link>
    <!-- se id == node_id -->
    <node id="urn:publicid:jgnx-se1" type="se">
      <!-- defined by Roberto-san's request -->
      <management type="snmp">
        <address>192.168.1.2</address>
        <port>161</port>
        <auth_id>monitoring</auth_id>
        <auth_pass>felix_monitoring</auth_pass>
      </management>
      <interface id="urn:publicid:jgnx-se1:if1">
          <!-- port number(interface name?) == port num -->
          <port num="eth1"/>
      </interface>
      <interface id="urn:publicid:jgnx-se1:if2">
          <port num="eth2"/>
      </interface>
    </node>
    <!-- SE: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:jgnx-se1:if1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11"/>
    </link>
    <!-- tn id == node_id -->
    <node id="urn:publicid:tn-network1" type="tn">
      <interface id="urn:publicid:tn-network1+urn:felix:jgnx-stp1"/>
    </node>
    <!-- TN: { 1st interface_ref: source interface, 2nd interface_ref: destination interface } -->
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:jgnx-stp1"/>
      <interface_ref client_id="urn:publicid:jgnx-se1:if2"/>
    </link>
  </topology>
</topology_list>
```

'''GET topology'''
`$ curl -X GET http://127.0.0.1:8448/monitoring-system/topology/physical`

e.g. response topology xml
```
<?xml version="1.0" ?>
<topology_list>
  <topology last_update_time="1412670730" name="urn:publicid:IDN+ocf:i2cat" type="physical">
    <node id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer" type="server">
      <interface id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
    </node>
    <node id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12">
        <port num="12"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10">
        <port num="10"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_11">
        <port num="11"/>
      </interface>
    </node>
    <node id="urn:publicid:i2cat-se1" type="se">
      <interface id="urn:publicid:i2cat-se1:if1">
        <port num="eth1"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if2">
        <port num="eth2"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if3">
        <port num="eth3"/>
      </interface>
      <interface id="urn:publicid:i2cat-se1:if4">
        <port num="eth4"/>
      </interface>
    </node>
    <node id="urn:publicid:tn-network1" type="tn">
      <interface id="urn:publicid:tn-network1+urn:felix:i2cat-stp1"/>
      <interface id="urn:publicid:tn-network1+urn:felix:i2cat-stp2"/>
    </node>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:i2cat:vtam:Verdaguer+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_12"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:i2cat-se1:if1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_10"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:i2cat-se1:if2"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:02_11"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:i2cat-stp1"/>
      <interface_ref client_id="urn:publicid:i2cat-se1:if3"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:i2cat-stp2"/>
      <interface_ref client_id="urn:publicid:i2cat-se1:if4"/>
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
    <node id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03" type="switch">
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11">
        <port num="11"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1">
        <port num="1"/>
      </interface>
      <interface id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_15">
        <port num="15"/>
      </interface>
    </node>
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server1" type="server">
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server1+interface+eth1"/>
    </node>
    <node id="urn:publicid:IDN+ocf:jgnx:vtam:server2" type="server">
      <interface id="urn:publicid:IDN+ocf:jgnx:vtam:server2+interface+eth2"/>
    </node>
    <node id="urn:publicid:jgnx-se1" type="se">
      <interface id="urn:publicid:jgnx-se1:if1">
        <port num="eth1"/>
      </interface>
      <interface id="urn:publicid:jgnx-se1:if2">
        <port num="eth2"/>
      </interface>
    </node>
    <node id="urn:publicid:tn-network1" type="tn">
      <interface id="urn:publicid:tn-network1+urn:felix:jgnx-stp1"/>
    </node>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_6"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_1"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:jgnx:vtam:server1+interface+eth1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:01_13"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:IDN+ocf:jgnx:vtam:server2+interface+eth2"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_15"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:jgnx-se1:if1"/>
      <interface_ref client_id="urn:publicid:IDN+openflow:ocf:jgnx:ofam+datapath+00:00:00:00:00:00:00:03_11"/>
    </link>
    <link type="lan">
      <interface_ref client_id="urn:publicid:tn-network1+urn:felix:jgnx-stp1"/>
      <interface_ref client_id="urn:publicid:jgnx-se1:if2"/>
    </link>
  </topology>
</topology_list>
```
