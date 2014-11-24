Resource Orchestrator
=====================

Aim
---
To orchestrate or coordinate the end-to-end network service and resource reservations.

Installing
----------
1. ``cd deploy``, assuming you are located at the RO root path (where this README is located)
1. ``./install.sh`` to install dependencies and add entries for dummy RMs to the RO's ``RoutingTable``

Running
-------
1. ``cd src``, assuming you are located at the RO root path (where this README is located)
1. ``python main.py`` runs the flask server for RO
  * You may now access RO at ``https://127.0.0.1:8440/xmlrpc/geni/3/``
