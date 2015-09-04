OVERVIEW OF KVM-CRM
===================

FELIX KVM-based Compute Resource Manager (KVM-CRM) is a KVM-based virtual 
machine (VM) management software for testbed management. It based on OFELIA 
Control Framework (OCF).
It controls experimentation life-cycle; reservation,
instantiation, configuration, monitoring and uninistantiation.

KVM-CRM replaces some of components of XEX-based OCF to use KVM.
So the KVM-CRM package provides only a VT manager for KVM (KVM-VT) 
and KVM-based OXAD (KVM-OXAD). KVM-VT is a master server of KVM-CRM
and KVM-OXAD is a KVM agent for virtualization purposes. 



INSTALLING KVM-CRM
==================

# 1. Requirements


* KVM-VT (VT manager for KVM)
  * One (or more) GNU/Linux Debian-based distros
  * Developed and ensured to work under Debian 7.0 (Wheezy) using
    the following packages:
    * Python 2.7
    * Django 1.4.19 (automatically installed)
    * MySQL server (automatically installed)
* KVM-OXAD (KVM agent for virtualization purposes)
  * Ubuntu 14.04 or later
  * Developed and ensured to work under Ubuntu 14.04 (or later) using
    the following packages:
    * libvirt-bin
    * qemu-kvm
    * Python 2.7
    * Django 1.4.19
    * MySQL server


# 2. Installing

## 2.1 Clone the KVM-CRM repository:

    mkdir -p /opt/felix/ocf
    git clone https://github.com/dana-i2cat/felix.git /opt/felix/ocf
    cd /opt/felix/ocf
    git checkout kvm-crm

## 2.2 For KVM-VT: choose the components to install as a root user. 

    cd /opt/felix/ocf/deploy
    python install.py

    The following actions will take place: 
    * Install dependencies
    * Build Certificates (see Note #1)
    * Configure Apache
    * Set file permissions
    * Modify the localsettings.py or mySettings.py depending on the 
      component being installed
    * Populate database

    Note #1: When installing the component, you will need to create the
    certificates for the Certification Authority (CA) first and for the
    component later. Do not use the same Common Name (CN) for both of them,
    and make sure that the CN you use in the component later certificate
    (you can use an IP) is the same you then set in the SITE_DOMAIN field
    in the localSettings.py file.

## 2.3 For KVM-OXAD:

### 2.3.1 Install packages

    apt-get install openssl ssl-cert \
        python-setuptools qemu-kvm libvirt-bin tshark python-libvirt \
        python-setuptools python-mysqldb python-openssl python-m2crypto \
        python-dateutil python-decorator python-paramiko build-essential \
        python-imaging python-configobj python-pyparsing \
        python-lxml python-argparse python-pexpect python-dev libldap2-dev \
        libsasl2-dev libguestfs-tools libpython-stdlib python-pip git
    pip install --allow-external django-evolution \
        "django-evolution<=0.6.9" pytz "Django<=1.4.19" \
        "django-extensions<=1.2.5" django-autoslug django-auth-ldap \
        django-registration jinja2 

### 2.3.2 Configure libvirt

- Open /etc/libvirt/qemu.conf and add (or modify) following parameters:

        user = "root"
        group = "root"
        
- Restert libvirt-bin

        service libvirt-bin restart

- Create bridge to connect the NICs of user VM

        brctl addbr brx0
        brctl addif brx0 eth0

### 2.3.3 Set up disk image files

#### 2.3.3.1 Create directories for disk image files

Most of directories created in this section should be specified
in configuration file (see section 2.3.5)

    mkdir -p /mnt/l1vm
    # Disk image template folder
    mkdir -p /mnt/l1vm/template
    # Log folder
    mkdir -p /mnt/l1vm/image/log
    # Cache folder to store VMs
    # It must be same as OXA_FILEHD_CACHE_VMS in configuration file.
    mkdir -p /mnt/l1vm/image/cache/vms
    # Remote folder to store VMs 
    # It must be same as OXA_FILEHD_REMOTE_VMS in configuration file.
    mkdir -p /mnt/l1vm/image/remote/vms 
    # Cache folder for templates 
    # It must be same as OXA_FILEHD_CACHE_TEMPLATES in configuration file.
    mkdir -p /mnt/l1vm/image/cache/templates
    # Remote folder for templates
    # It must be same as OXA_FILEHD_REMOTE_TEMPLATES in configuration file.
    mkdir -p /mnt/l1vm/image/remote/templates

#### 2.3.4.2 Generate disk image template

Change directory to
`/opt/felix/ocf/vt_manager/src/python/agent/utils/generate_template` 
and run `generate_template` script as root. When finished,
a template file `l1vm.qcow2` is generated in `/mnt/l1vm/template` directory.

    cd /opt/felix/ocf/vt_manager/src/python/agent/utils/generate_template
    ./generate_template
    
### 2.3.5 Create KVM-OXAD configuration files

    cd /opt/felix/ocf/vt_manager/src/python/agent/
    vi mySettings.py

- mySettings.py

        ### Section 1: KVM-OXAD settings
        #
        # Basic settings for the KVM-OXAD
        # Settings for virtualization KVM-VT, to which the KVM-OXAD connects
        # VTAM_PORT: it is usually '8445'
        # WARNING: *same* settings as in KVM-VT's 'mySettings.py' file
        VTAM_IP = "172.21.100.137"
        VTAM_PORT = "8445"
        XMLRPC_USER = "root"
        XMLRPC_PASS = "password"
        
        # Password for the KVM-OXAD HTTP XML-RPC server. Use a STRONG password
        XMLRPC_SERVER_PASSWORD = "password"
        
        ### Section 2: Optional KVM-OXAD settings
        #
        # Optional settings for the KVM-OXAD.
        # WARNING: default values are commented. Uncomment and modify to override
        # the static settings (file at 'settings/staticSettings.py').
        #
        # Network parameters.
        # XMLRPC_SERVER_LISTEN_HOST: you should not use '' here
        # unless you have a real FQDN.
        # Defaults are as follows.
        ##XMLRPC_SERVER_LISTEN_HOST = "0.0.0.0"
        ##XMLRPC_SERVER_LISTEN_PORT = 9229
        
        # Enable/Disable the usage of cache.
        # Default is True.
        ##OXA_FILEHD_USE_CACHE = True
        
        # Use sparse disks or not while cloning.
        # Uncomment if willing to use Sparse disks.
        # Default is False.
        ##OXA_FILEHD_CREATE_SPARSE_DISK = False
        
        # Define machine SWAP size in MB.
        # Default is 512.
        ##OXA_DEFAULT_SWAP_SIZE_MB = 512
        
        # Level used for logging Agent messages.
        # Possible values = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}.
        # Default is "WARNING".
        #
        LOG_LEVEL = "DEBUG"
        
        #Template Image File location
        OXA_KVM_DEBIAN_TEMPLATE_IMGFILE="/mnt/l1vm/template/l1vm.qcow2"
        OXA_KVM_UBUNTU_TEMPLATE_IMGFILE="/mnt/l1vm/template/l1vm.qcow2"
        
        ## FileHD driver settings
        # Enable/disable file-type Hdmanager Cache FS
        OXA_FILEHD_USE_CACHE=False
        
        # Cache folder to store VMs (if cache mechanism is used)
        OXA_FILEHD_CACHE_VMS="/mnt/l1vm/image/cache/vms/"
        
        # Remote folder to store VMs
        OXA_FILEHD_REMOTE_VMS="/mnt/l1vm/image/remote/vms/"
        
        # Cache folder for templates (if cache is enabled)
        OXA_FILEHD_CACHE_TEMPLATES="/mnt/l1vm/image/cache/templates/"
        
        # Remote folder for templates
        OXA_FILEHD_REMOTE_TEMPLATES="/mnt/l1vm/image/remote/templates/"
        
        # Use sparse disks while cloning
        OXA_FILEHD_CREATE_SPARSE_DISK=False
        
        # Nice priority for Copy&untar operations
        OXA_FILEHD_NICE_PRIORITY=15
        
        # IONice copy&untar operations class
        OXA_FILEHD_IONICE_CLASS=2
        
        # IONice copy&untar operations priority
        OXA_FILEHD_IONICE_PRIORITY=5
        
        # /bin/dd block size(bs) for copy operations
        OXA_FILEHD_DD_BS_KB=32

### 2.3.6 Register KVM-OXAD to KVM-VT (at KVM-VT node)

    Note: Values should be changed to fit your environment.
    The followings are an example of settings.
    
    mysql -u root -p ocf__vt_manager 

- Register KVM-OXAD

        INSERT INTO vt_manager_vtserver VALUES (\
            1,        /* id: ID of KVM-OXAD, must be unique */ \
            0,        /* available: KVM-OXAD is available or not, 1 is available */ \
            1,        /* enabled: KVM-OXAD is enable or not, 1 is enable */ \
            'test1',  /* name: Name of KVM-OXAD */ \
            'uuid1',  /* uuid: UUID of KVM-OXAD */ \
            'Linux',  /* operatingSystemType: OS type running KVM-OXAD */ \
            'Ubuntu', /* operatingSystemDistribution: OS distribution type running KVM-OXAD */ \
            '14.04',  /* operatingSystemVersion: OS version running KVM-OXAD */ \
            'kvm',    /* virtTech: Hypervisor type of KVM-OXAD, must be 'kvm' for KVM-OXAD */ \
            1,        /* numberOfCPUs: Number of CPUs in KVM-OXAD node */ \
            2000,     /* CPUFrequency: CPU clock (units in MHz) of KVM-OXAD node */ \
            1024,     /* memory: Memory (units in MB) of KVM-OXAD node */ \
            1024,     /* discSpaceGB: Disk size (units in GB) of KVM-OXAD node */ \
            'http://172.21.100.11:9229/', /* agentURL: URL of KVM-OXAD */ \
            'password',                   /* agentPassword: Password to access the URL */ \
            'http://172.21.100.11:9229/'  /* url: URL of KVM-OXAD node, normally same as agentURL */);

- Register KVM-OXAD as KVM hypervisor

        INSERT INTO vt_manager_kvmserver VALUES (\
            1 /* vtserver_ptr_id: ID of KVM-OXAD, must be same as vt_manager_vtserver.id */);

- Register IP address range to allocate to user VM

        INSERT INTO vt_manager_ip4range VALUES (\
            1,                 /* id: ID of the range, must be unique */ \
            'ip1',             /* name: Name of the range */
            1,                 /* isGlobal: 1 if the range is global IP, 0 is local */ \
            '192.168.123.2',   /* startIp: Start IP address the range */ \
            '192.168.123.254', /* endIp: End IP address the range */ \
            '255.255.255.0',   /* netMask: Subnet mask of the range */ \
            '192.168.123.1',   /* gw: Gateway of the range */ \
            '10.1.100.1',      /* dns1: DNS address for the range (optional) */ \
            '8.8.8.8',         /* dns2: Secondary DNS address for the range (optional) */ \
            '192.168.123.2',   /* nextAvailableIp: Next allocatable IP address */ \
            253                /* numberOfSlots: Number of IP addresses of the range */ \);

- Register MAC address range to allocate to user VM

        INSERT INTO vt_manager_macrange VALUES (\
            1,                   /* id: ID of the range, must be unique */ \
            'mac1',              /* name: Name of the range, must be unique */ \
            1,                   /* isGlobal: 1 if the range is global MAC, 0 is local */ \
            '52:54:01:00:00:01', /* startMac: Start MAC address the range */ \
            '52:54:01:00:00:ff', /* endMac: End MAC address the range */ \
            '52:54:01:00:00:02', /* nextAvailableMac: Next allocatable MAC address */ \
            254                  /* numberOfSlots: Number of MAC addresses of the range */);

- Register MAC address of a bridge of KVM-OXAD node as a slot

        INSERT INTO vt_manager_macslot VALUES (\
            1001,                /* id: ID of the slot, must be unique */ \
            '52:54:01:00:00:01', /* mac: MAC address of the slot */ \
            1,                   /* macRange_id: ID of the range, must be same as vt_manager_macrange.id */ \
            1,                   /* isExcluded: 1 if this slot is excluded from allocation, 0 otherwise */ \
            'comment'            /* comment: Comment of the slot */ );

- Register a bridge of KVM-OXAD node to provide for user VM

        INSERT INTO vt_manager_networkinterface VALUES (\
            101,    /* id: ID of the interface, must be unique */ \
            'brx0', /* name: Interface name, must be same as actual interface */ \
            1001,   /* mac_id: MAC address slot of the interface, must be same as vt_manager_macslot.id */ \
            1,      /* isMgmt: 1 if this interface is used for management, 0 otherwise */ \
            1,      /* isBridge: 1 if this interface is bridge, 0 is actual NIC */ \
            'brx0', /* switchID: Switch name, must be same as vt_manager_networkinterface.name if this interface is bridge */ \
            1,      /* port: Number of port on this interface, normally 1 */ \
            1       /* idForm: currently unused */);

- Allocate a bridge to KVM-OXAD node as an interface

        INSERT INTO vt_manager_vtserver_networkInterfaces VALUES (\
            1,  /* id: ID of the allocation, must be unique */ \
            1,  /* vtserver_id: ID of the KVM-OXAD, must be same as vt_manager_vtserver.id */ \
            101 /* networkinterface_id: ID of the interface, must be same as vt_manager_networkinterface.id */ );


- Allocate the IP address ranges to KVM-OXAD node

        INSERT INTO vt_manager_vtserver_subscribedIp4Ranges VALUES (\
        1, /* id: ID of the allocation, must be unique */ 
	1, /* vtserver_id: ID of the KVM-OXAD, must be same as vt_manager_vtserver.id*/ 
	1  /* ip4range_id: ID of IP address range to allocate, must be same as vt_manager_ip4range.id*/ );


# 3. Additional notes

Please have a look to Manuals [https://github.com/dana-i2cat/felix/wiki]
for further component configuration.


FURTHER READING
===============

For more information about configuration, troubleshooting, contribution and
so on please visit https://github.com/dana-i2cat/felix/wiki


COPYRIGHT
=========

Copyright (C) 2015
National Institute of Advanced Industrial Science and Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

