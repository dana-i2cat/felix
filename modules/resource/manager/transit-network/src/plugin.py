# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import amsoil.core.pluginmanager as pm
from tn_rm_delegate import TNRMGENI3Delegate

def setup():
    # setup config keys
    # config = pm.getService("config")

    xmlrpc = pm.getService('xmlrpc')
    handler = pm.getService('geniv3handler')
    xmlrpc.registerXMLRPC('tn_rm_geni_v3', handler, '/xmlrpc/geni/3/')
    delegate = TNRMGENI3Delegate()
    handler.setDelegate(delegate)

