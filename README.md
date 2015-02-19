Resource Orchestrator
=====================

Aim
---
To orchestrate or coordinate the end-to-end network service and resource reservations.

Installing
----------
1. ``cd modules/resource/orchestrator/deploy``
1. ``./install.sh`` to install dependencies and add entries for dummy RMs to the RO's ``RoutingTable``

Managing entries for your RMs
-----------------------------
1. ``cd modules/resource/orchestrator/src/admin/db``
1. You may add, delete or dump entries so that RO can communicate with your RMs:
  *  Syntax: ``python manage.py [add_route_entry|delete_route_entry|dump] [params]``
    * Parameters (only for add/delete):
      * ``$type`` can be one of _virtualisation_, _sdn_networking_, _stitching_entity_ or _transport_network_
      * ``$host_ip``, ``$host_port`` is the IP and port where the RM is listening
      * ``$protocol`` is usually _https_ or _http_
      * ``$am_type``, ``$am_version``, usually set to type _geni_ and version _3_
      * ``$endpoint`` URI where the API is exposed, e.g. _/xmlrpc/geni/3/_
      * Others: ``--user``, ``--password`` may be added iff needed to provide BasicAuth
  *  Adding entry: ``python manage.py add_route_entry -t "$type" -a "$host_ip" -p "$host_port" --protocol "$protocol" --endpoint "$endpoint" --am_type "$am_type" --am_version $am_version``
  * Removing entry: ``python manage.py delete_route_entry -t "$type" -a "$host_ip" -p "$host_port" --protocol "$protocol" --endpoint "$endpoint" --am_type "$am_type" --am_version $am_version``
  *  Dumping all entries: ``python manage.py dump``

Running
-------
1. ``cd modules/resource/orchestrator/src``
1. ``python main.py`` runs the flask server for RO
  * You may now access RO at ``https://127.0.0.1:8440/xmlrpc/geni/3/``

Configuring GCF and omni
------------------------
[OMNI](http://trac.gpolab.bbn.com/gcf/wiki/Omni) is a CLI that is part GCF (GENI Control Framework). This allows reserving, provisioning and managing resources at GENI aggregate managers. After [configuring](http://trac.gpolab.bbn.com/gcf/wiki/OmniConfigure/Manual) this environment, you will be able to send requests against the GENI API v3 of your RO or RM. See "Testing RO with omni" for details.

Running GCF ClearingHouse
-------------------------
The GENI ClearingHouse provides credentials to every method issued by omni. Therefore, the GCF CH must be running beforehand. The default port used by the CH is ``8000``.

```
python src/gcf-ch.py
```

If everything is working properly you should see something like this:

```
INFO:cred-verifier:Will accept credentials signed by any of 1 root certs found in ~/.gcf/trusted_roots: ['~/.gcf/trusted_roots/ch-cert.pem']
INFO:gcf-ch:Registering AM urn:publicid:IDN+geni:gpo:gcf:am1+authority+am at http://localhost:8001
INFO:cred-verifier:Adding trusted cert file ch-cert.pem
INFO:cred-verifier:Combined dir of 1 trusted certs ~/.gcf/trusted_roots into file ~/.gcf/trusted_roots/CATedCACerts.pem for Python SSL support
INFO:gcf-ch:GENI CH Listening on port 8000...
```

Testing RO with omni
--------------------
After the configuration step is properly finished (see "Configuring GCF and omni"), assume your RM is located at ``https://localhost:8401`` and send any of the desired commands:

```
# Retrieve version and meta information of the RM
python src/omni.py -o -a https://localhost:8401 -V 3 --debug getversion
# Retrieve list of resources provided by the RM (e.g. servers for CRM, switches for SDNRM)
python src/omni.py -o -a https://localhost:8401 -V 3 --debug --no-compress listresources
# Retrieve contents (slivers) belonging to a given slice
python src/omni.py -o -a https://localhost:8401 -V 3 --debug describe slicename
# Reserve/Allocate resources within a slice. (Parameter "--end-time" optional)
python src/omni.py -o -a https://localhost:8401 -V 3 --debug allocate slicename rspec-req.xml --end-time=2014-04-12T23:20:50.52Z
# Renew time where resources from reservation/allocation are kept from other users
python src/omni.py -o -a https://localhost:8401 -V 3 --debug renew slicename 2013-02-07T15:00:50.52Z
# Provision the resources previously allocated. (Parameter "--end-time" optional)
python src/omni.py -o -a https://localhost:8401 -V 3 --debug provision slicename --end-time=2014-04-12T23:20:50.52Z
# Retrieve status of a given slice
python src/omni.py -o -a https://localhost:8401 -V 3 --debug status slicename
# Perform action over a resource or sliver. Actions are usually: [geni_start | geni_stop | geni_restart]
python src/omni.py -o -a https://localhost:8401 -V 3 --debug performoperationalaction slicename geni_start
# Delete a given slice and all its contents
python src/omni.py -o -a https://localhost:8401 -V 3 --debug delete slicename
# Shut down a given slice and all its contents. Intended for admin/operator use, not user's
python src/omni.py -o -a https://localhost:8401 -V 3 --debug shutdown slicename
```

Example CRM RSpec for rspec-req.xml:
```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<rspec type="request"
    xs:schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/request.xsd"
    xmlns="http://www.geni.net/resources/rspec/3"
    xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:emulab="http://www.protogeni.net/resources/rspec/ext/emulab/1">
  <node client_id="Verdaguer" component_id="urn:publicid:IDN+ocf:i2cat:vtam+node+Verdaguer" component_manager_id="urn:publicid:IDN+ocf:i2cat:vtam+authority+cm" exclusive="true">
      <sliver_type name="emulab-xen">
        <emulab:xen cores="3" ram="1024" disk="10"/>
        <disk_image name="urn:publicid:IDN+wall2.ilabt.iminds.be+image+emulab-ops//DEB60_64-VLAN"/>
     </sliver_type>
  </node>
         <node client_id="Rodoreda" component_id="urn:publicid:IDN+ocf:i2cat:vtam+node+Rodoreda" component_manager_id="urn:publicid:IDN+ocf:i2cat:vtam+authority+cm" exclusive="true">
      <sliver_type name="emulab-xen">
        <emulab:xen cores="3" ram="1024" disk="10"/>
        <disk_image name="urn:publicid:IDN+wall2.ilabt.iminds.be+image+emulab-ops//DEB60_64-VLAN"/>
     </sliver_type>
  </node>
</rspec>
```

If everything is working properly you should see something like this:

```
Result Summary: Slice urn:publicid:IDN+geni:gpo:gcf+slice+slicename expires in <= 3 hours on ...
Reserved resources on https://localhost:8401.
Saved createsliver results to slicename-manifest-rspec-localhost-8401.xml.
```
