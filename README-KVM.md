===================
OVERVIEW OF OCF-KVM
===================

OFELIA Control Framework for KVM (OCF-KVM) is a set of software tools
for testbed management. It based on OFELIA Control Framework (OCF).
It controls experimentation life-cycle; reservation,
instantiation, configuration, monitoring and uninistantiation.

Features:

OCF-KVM replaces some of components of OCF to use KVM.
So OCF-KVM provides only CRM-KVM (VT manager for KVM) and OXAD-KVM (KVM agent
for virtualization purposes). 
OCF-KVM is currently deployed in OFELIA FP7 project testbed, the European
Openflow testbed. The ideas behind its architecture are heavily influenced
by the experience of other testbed management tools and GENI architectural
concepts. Take a look at Overview section for more details.


==================
INSTALLING OCF-KVM
==================

1. Requirements
---------------

* CRM-KVM (VT manager for KVM)
  * One (or more) GNU/Linux Debian-based distros
  * Developed and ensured to work under Debian 7.0 (Wheezy) using
    the following packages:
    * Python 2.7
    * Django 1.4.5 (automatically installed)
    * MySQL server (automatically installed)
* OXAD-KVM (KVM agent for virtualization purposes)
  * Ubuntu 14.04 or later
  * Developed and ensured to work under Ubuntu 14.04 (or later) using
    the following packages:
    * qemu-kvm
    * Python 2.6
    * libvirt-bin  (automatically installed)
    * Django 1.2.3 (automatically installed)
    * MySQL server (automatically installed)


2. Installing
-------------

2.1 Clone the OCF-KVM repository:

    git clone ssh://163.220.30.137/opt/felix/ocf /opt/felix/ocf
    cd /opt/felix/ocf
    git checkout ocf-kvm

    Alternatively you can download the tarball and uncompress in place

2.2 For CRM-KVM: choose the components to install 
    as a root user. This will implicitly trigger OFVER:

    cd /opt/felix/ocf/deploy
    python install.py

    The following actions will take place: 
    * Install dependencies
    * Build Certificates (see Note #2)
    * Configure Apache
    * Set file permissions
    * Modify the localsettings.py or mySettings.py depending on the 
      component being installed
    * Populate database
    * When installation starts, ofver will ask if it is an OFELIA
      project installation or not. Select No (N) for non OFELIA testbeds.

    Note #2: When installing the component, you will need to create the
    certificates for the Certification Authority (CA) first and for the
    component later. Do not use the same Common Name (CN) for both of them,
    and make sure that the CN you use in the component later certificate
    (you can use an IP) is the same you then set in the SITE_DOMAIN field
    in the localsettings.py file.

2.3 For OXAD-KVM (KVM agent for virtualization purposes):

    Trigger OFVER install by performing the following as a root user (see Note #3):

    cd /opt/felix/ocf/vt_manager/src/python/agent/tools
    ./ofver install

    Note #3: When installation starts, ofver will ask if it is an OFELIA project 
    installation or not, and accordingly ofver will download the VMs templates 
    from the proper storage.


3. Upgrading
------------

3.1 For CRM-KVM: choose the components to install as a 
    root user. This will implicitly trigger OFVER:

    cd /opt/felix/ocf/deploy
    python upgrade.py

3.2 For OXAD-KVM:

    cd /opt/felix/ocf/vt_manager/src/python/agent/tools
    ./ofver upgrade


4. Migrating
------------

4.1 For CRM-KVM: choose the new path in your servers 
    where you want the OCF stack code to be migrated:

    cd /opt/felix/ocf/deploy
    python migrate.py

4.2 For OXAD-KVM:
    Sorry, this features is not supported


5. Additional notes
-------------------

Please have a look to Manuals [https://github.com/fp7-ofelia/ocf/wiki/Manuals]
for further component configuration.

You can use -f force flag on OFVER to force installation/upgrade. Take a look
at ./ofver -h for more details.


===============
FURTHER READING
===============

For more information about configuration, troubleshooting, contribution and
so on please visit https://github.com/fp7-ofelia/ocf/wiki

=========
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

