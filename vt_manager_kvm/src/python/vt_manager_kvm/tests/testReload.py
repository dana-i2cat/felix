#!/usr/bin/python
import sys,os
sys.path.append("/opt/ofelia/vt_manager_kvm/src/python/vt_manager_kvm")
import vt_manager_kvm.models

for i in range(0,100):
    for mod in sys.modules:
        if mod.startswith('vt_manager_kvm.models'):
            #print mod
            del mod

    import vt_manager_kvm.models 
