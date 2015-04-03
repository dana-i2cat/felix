import os
import sys
from os.path import dirname, join

PYTHON_DIR = join(dirname(__file__), '../../python')

# This is needed because wsgi disallows using stdout
sys.stdout = sys.stderr

os.environ['DJANGO_SETTINGS_MODULE'] = 'vt_manager.settings.settingsLoader'



#sys.path.append(PYTHON_DIR)
sys.path.insert(0,PYTHON_DIR)


from django.contrib.auth.models import User
from django import db
from vt_manager.settings.settingsLoader import XMLRPC_USER, XMLRPC_PASS
import re

AGENT_RE = "^/xmlrpc/agent/?$"
PLUGIN_RE = "^/xmlrpc/plugin/?$"

def check_password(environ, user, password):
    db.reset_queries()
    kwargs = {'username': user, 'is_active': True}
    pattern_agent = re.compile(AGENT_RE)
    pattern_plugin = re.compile(PLUGIN_RE)

    try:
        print("user = " + user + ", password = " + password)
        print("XMLRPC_USER = " + XMLRPC_USER + ", XMLRPC_PASS = " + XMLRPC_PASS)
        if pattern_plugin.match(environ['REQUEST_URI']) or pattern_agent.match(environ['REQUEST_URI']):
            if user == XMLRPC_USER and password == XMLRPC_PASS:
                print("password check for agent/plugin OK")
                return True
#            else:
#                return False
#        else:
        try:
            user = User.objects.get(**kwargs)
            user.set_password(XMLRPC_PASS)
        except User.DoesNotExist:
            print("User.DoesNotExist, check NG")
            return None

        if user.check_password(password):
            print("check_password() OK")
            return True
        else:
            print("check_password() NG")
            return False
    finally:
        db.connection.close()
