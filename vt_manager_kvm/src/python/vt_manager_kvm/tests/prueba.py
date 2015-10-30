import os
import sys
from os.path import dirname, join

PYTHON_DIR = join(dirname(__file__), '/opt/ofelia/vt_manager_kvm/src/python/')

# This is needed because wsgi disallows using stdout
sys.stdout = sys.stderr

os.environ['DJANGO_SETTINGS_MODULE'] = 'vt_manager_kvm.settings'

sys.path.insert(0,PYTHON_DIR)


from vt_manager_kvm.controller.drivers.Driver import Driver

drivers = Driver.getAllDrivers()

print drivers


