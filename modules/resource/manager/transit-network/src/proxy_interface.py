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

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from abc import ABCMeta, abstractmethod

# class Handler(SimpleXMLRPCRequestHandler):

class Proxy:
    __metaclass__ = ABCMeta

    @abstractmethod
    def reserve(resv):
        pass

    @abstractmethod
    def modify(resv, end_time_sec):
        pass

    @abstractmethod
    def provision(resv):
        pass

    @abstractmethod
    def release(resv):
        pass

    @abstractmethod
    def terminate(resv):
        pass
