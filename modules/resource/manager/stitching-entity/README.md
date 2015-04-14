Stitching Entity Resource Manager
=================================


# Requirements and Dependencies

This is the list of requirements and dependencies to install SE-RM. Basically, it needs a Linux-based operating system with installed Python runtime environment extended with Python libraries listed in this section. Moreover, it requires locally installed MongoDB database.

## Requirements
The tested working environment ia a Debian-based distribution. Specifically, the module was tested both on <b>Debian 7 (Wheezy)</b> and <b>Ubuntu Ubuntu 14.04.1 LTS (Trusty Tahr)</b>. Althought, it should run on other Linux-based operation systems if all needed dependencies can be satisfied. SE-RM module needs the MongoDB database instance to be installed and configured to be available from the module by localhost interface and default port that is <i>27017</i>. The module connects to the MongoDB server and assumes a default database name of <i>felix_se</i>. A helper install and configuration scripts can be find in deploy directory (see section "Configuration and Installation").

## Dependencies
There is a number of packages required for SE-RM to work. These are retrieved & installed by Debian's Advanced Packaging Tool (apt-get) or the Python version system (easy_install, pip).

### Advanced Packaging Tool (APT)
The following Debian packages must be installed on the system for SE-RM to properly work:

```
 libssl-dev python-m2crypto build-essential python-all-dev libssl-dev 
 swig python-setuptools openssl mongodb-server
```

### Python Package Index (PIP)
The following python packages must be installed on the system for SE-RM to properly work:

```
 python-dateutil pyyaml pyopenssl m2crypto lxml pymongo apscheduler
 requests flask flask-pymongo blinker flup argparse Flask-XML-RPC
 networkx
```

## Configuration and Installation

### Installation
Get the source code from git repository and switch to ''stitching-element'' branch:

```
 $ git clone https://github.com/dana-i2cat/felix.git
 $ git checkout stitching-entity
```

Now, enter the SE-RM's deploy directory and run the installation script (root account or sudo is needed):

```
 $ cd felix/modules/resource/manager/stitching-entity/deploy/
 $ ./install.sh
```

All the required Debian packages and Python libraries should be installed automatically. Enter the module's root directory. The default SE-RM installation is supplied with a template configuration file. The module can be now run with this example configuration but will not be operating on real resources. Please make sure you proceed with the next step "Configuration" before running the final instance. To run the SE-RM, go to ''src'' directory and run the ''main.py'' script:

```
 $ cd src/
 $ python main.py
```

Logs are collected in ```log/stitching-entity.log```

###  Configuration
The SE-RM configuration can be changed in set of files in ''conf/'' directory. Below the description of each configuration file is given.

#### se-config.yaml

This configuration file contains a list of ports on Stitching Element that are under SE-RM management. For each port the VLANs that take part in translating can be specified or alternatively, the remote endpoint label of static link. Besides, the transport VLAN setting can be chosen (QinQ, VLAN translation). The configuration also contains SE-RM Rspec specific parameters like, URN identifiers or link capacity. Please note that this configuration is a YAML file and suggested syntax for YAML files is to use two spaces for indentation however YAML follows whatever indentation system is employed. In the following an example configuration file is presented.

```yaml
organisation: psnc
dpid: 00:00:00:00:00:00:00:01

vlan_trans: true
qinq: false
capacity: 1G


interfaces:
    "1":
        remote_endpoints: 
            -
                name: urn:publicid:IDN+fms:i2cat:tnrm+stp+urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:05_10
                type: vlan_trans
                vlans:
                    - 1000
            -
                name: urn:publicid:IDN+fms:i2cat:tnrm+stp+urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:05_11
                type: vlan_trans
                vlans:
                    - 2001

    "2":
        remote_endpoints:
            -
                name: urn:publicid:IDN+openflow:ocf:i2cat:ofam+datapath+00:10:00:00:00:00:00:05_6
                type: static_link
                vlans:
                    - 1001

```

#### XML-RPC Server
* ```flask.conf```
This file contains the properties of the FLASK XML-RPC Server [Flask] like IP address, port or debug mode.

```
[general]
	host = 0.0.0.0
	port = 8447
	debug = True

[fcgi]
	# Development server
	enabled = False
	port = 8450

[certificates]
	force_client_certificate = True
```

#### GENIv3
* ```geniv3.conf```
This file contains parameters of the RSpec validation mode and directory to the certificates.

```
[general]
	rspec_validation = True

[certificates]
	cert_root = cert/trusted
```

#### Logging
* ```log.conf```
This file contains the Logger parameters like logging format, level or output filename.

```
[general]
	name = stitching-entity
	level = logging.DEBUG
	format = %(asctime)s [%(levelname)s] - %(message)s
	file = stitching-entity.log
```


### Operation

The SE-RM can be tested as a standalone application without RO thanks to compatibilty with a 3rd party command line tool Omni [Omni]. This tool is shipped with GENI Control Framework (GCF) software package and allows to communicate with all FELIX RMs to make list the resources or make the reservations.
To use the Omni tool the Clearing House (CH) should be installed and deployed. In addition, the certificate keys should be exchanged between the Clearing House, Omni and SE-RM.

#### List Resources
To list resources from running SE-RM enter the Omni directory and run command:

```
$ python src/omni.py -o -a https://127.0.0.1:8447/xmlrpc/geni/3/ -V 3 --debug \
 -c ~/.gcf/omni_config --no-compress --available listresources
```

As a successful result the RSpec Manifest will be saved in the same directory and the summary will appear on on console output:

```
......
Wrote rspecs from 1 aggregate(s) to 1 file(s)
Saved listresources RSpec from 'unspecified_AM_URN' 
(url 'https://127.0.0.1:8447/xmlrpc/geni/3/') 
to file rspec-127-0-0-1-8447-xmlrpc-geni-3.xml;  
```

#### Allocate Slice
To allocate resources from running SE-RM enter the Omni directory and run command:

```
$ python src/omni.py -o -a https://127.0.0.1:8447/xmlrpc/geni/3/ -V 3 -c ~/.gcf/omni_config \
 --no-compress --available allocate example_slice_name \
 request_rspec_example.xml --end-time 201502312200
```

#### Delete Slice

```
$ python src/omni.py -o -a https://127.0.0.1:8447/xmlrpc/geni/3/ -V 3 -c ~/.gcf/omni_config \
 --no-compress --available delete example_slice_name
```

#### Parameters for operations

example_slice_name - urn name for allocated slice 

request_rspec_example.xml - example Rspec request slivers

```xml
    <?xml version="1.1" encoding="UTF-8"?>
    <rspec type="request"
           xmlns="http://www.geni.net/resources/rspec/3"
           xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
           xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
           xs:schemaLocation="http://www.geni.net/resources/rspec/3/request.xsd
                http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">

        <node client_id="urn:publicid:aist-se1"
              component_manager_id="urn:publicid:IDN+AIST+authority+serm">
            <interface client_id="urn:publicid:aist-se1:if2">
                <sharedvlan:link_shared_vlan name="urn:publicid:aist-se1:if2+vlan"
                                             vlantag="25"/>
            </interface>
            <interface client_id="urn:publicid:aist-se1:if3">
                <sharedvlan:link_shared_vlan name="urn:publicid:aist-se1:if3+vlan"
                                             vlantag="1983"/>
            </interface>
            
            <interface client_id="urn:publicid:aist-se1:if5">
                <sharedvlan:link_shared_vlan name="urn:publicid:aist-se1:if5+vlan"
                                             vlantag="55"/>
            </interface>
            <interface client_id="urn:publicid:aist-se1:if6">
                <sharedvlan:link_shared_vlan name="urn:publicid:aist-se1:if6+vlan"
                                             vlantag="1986"/>
            </interface> 
            
        </node>

        <link client_id="urn:publicid:aist-se1:if2-if3">
            <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
            <link_type name="urn:felix+vlan_trans"/>
            <interface_ref client_id="urn:publicid:aist-se1:if2"/>
            <interface_ref client_id="urn:publicid:aist-se1:if3"/>
        </link>
        
        <link client_id="urn:publicid:aist-se1:if5-if6">
            <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
            <link_type name="urn:felix+vlan_trans"/>
            <interface_ref client_id="urn:publicid:aist-se1:if5"/>
            <interface_ref client_id="urn:publicid:aist-se1:if6"/>
        </link> 
        
    </rspec>

```

# Ryu controller (SE-RM-OF-CTRL) for SE hardware OpenFlow compatible

SE-RM-OF-CTRL is a Stitching Element Resource Manager OpenFlow Controller entity. The module is responsible for provisioning OpenFlow resources in the SDN network. SE-RM-OF-CTRL build upon Ryu OF Controller configures OpenFlow switch and provides REST API interface towards SE-RM.

[Ryu REST API app documentation](http://ryu.readthedocs.org/en/latest/app/ofctl_rest.html)

##Installation

The following prerequisites are needed priot to install Ryu: 
* python-eventlet
* python-routes
* python-webob
* python-paramiko

```$ pip install ryu```

Or install from the source code:

```$ git clone git://github.com/osrg/ryu.git```
```$ cd ryu; python ./setup.py install```

##How to run SE-RM-OF-CTRL

```$ ~/ryu\> PYTHONPATH=. ./bin/ryu-manager --verbose ryu/app/ofctl_rest.py```
ofctl_rest is one of the built-in Ryu application.

###REST API interface

ryu.app.ofctl_rest provides REST APIs for retrieving the switch stats and Updating the switch stats. This application helps you debug your application and get various statistics. This application supports OpenFlow version 1.0, 1.2 and 1.3. [Ryu rest Api](http://ryu.readthedocs.org/en/latest/app/ofctl_rest.html)

##Example of use

To add flowmod whitch translates VLAN_ID=333 on in_port=12 to VLAN_ID=555 on out_port=13:
```bash
$ curl -X POST -d \
  '{"dpid":110533270894679, "cookie":1, "cookie_mask":1, "table_id":0, "idle_timeout":30, \
  "hard_timeout":30, "priority":1, "flags":1,  \
  "match":   {"dl_vlan":333, "in_port":12}, \
  "actions":[{"type":"SET_VLAN_VID","vlan_vid":555},{"type":"OUTPUT","port":13}]}' \
  http://localhost:8080/stats/flowentry/add
```

To delete above flowmode:
```bash
$ curl -X POST -d \
 '{"dpid":110533270894679, "cookie":1, "cookie_mask":1, "table_id":0, "idle_timeout":30, \
 "hard_timeout":30,  "priority":1, "flags":1, "match":{"dl_vlan":333, "in_port":12}, \
 "actions":[{"type":"SET_VLAN_VID","vlan_vid":555},{"type":"OUTPUT","port":13}]}' \
  http://localhost:8080/stats/flowentry/delete
```

##Deployment

SE-RM-OF-CTRL is deployed on VM(KVM) with ubuntu 13.04.
In PSNC SDN testbed SE-RM-OF-CTRL provision OF resources into Juniper MX80 (Junos 12.3 with OpenFlow v1.0).

###Slice configuration 
```
$ fvctl add-slice {slice_name} tcp:{of_contorller_ipv4:port} admin@{slice_name}
$ fvctl add-flowspace {flowspace_name} {dpid} 1 in_port={number} {slice_name}=7
                                          .....                        
```

##Ryu SE-RM REST plugin
The SE-RM component uses the Ryu REST application to install and delete the flows. The plugins' configuration file is located in: ```modules/resource/manager/stitching-entity/conf/ryu-config.yaml```  and looks like:

```yaml
host: 127.0.0.1
rest_port: 8080
dpid : 0000000000000001
```
After the proper configuration the plugin is connecting to Ryu controller using the REST API and provisions the flows.
