# -*- coding: utf-8 -*-

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

import libvirt
from utils.Logger import Logger
	
con = libvirt.openReadOnly(None)

class DomainMonitor:
	logger = Logger.getLogger()

	@staticmethod
	def retriveActiveDomainsByUUID(con):
		domainIds = con.listDomainsID()
		doms = list()

		for dId in domainIds:

			#Skip domain0
			if dId == 0:
				continue
	
			domain = con.lookupByID(dId)
			doms.append(domain.UUIDString())
			#DomainMonitor.logger.debug("Appending: "str(domain.UUIDString()))

		return doms 
