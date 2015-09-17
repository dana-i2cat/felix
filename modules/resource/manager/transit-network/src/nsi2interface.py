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

import sys
from datetime import datetime, timedelta
import time
import types
import log
logger = log.getLogger('tnrm:nsi2interface')
logger.info("start nsi2interface from TNRM to NSI.")

sys.path.append('/usr/share/java/')
#sys.path.append('../../common/build/jar/nsi2_common.jar')
sys.path.append('../../clientapi/build/jar/nsi2_client.jar')
sys.path.append('../libs/commons-logging-1.1.1.jar')
sys.path.append('../libs/log4j-1.2.13.jar')

sys.path.append('/opt/apache-cxf/lib/antlr-2.7.7.jar')
sys.path.append('/opt/apache-cxf/lib/aopalliance-1.0.jar')
sys.path.append('/opt/apache-cxf/lib/asm-3.3.jar')
sys.path.append('/opt/apache-cxf/lib/commons-collections-3.2.1.jar')
sys.path.append('/opt/apache-cxf/lib/commons-lang-2.6.jar')
sys.path.append('/opt/apache-cxf/lib/commons-logging-1.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-2.4.2.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-manifest.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-xjc-boolean-2.4.0.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-xjc-bug671-2.4.0.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-xjc-dv-2.4.0.jar')
sys.path.append('/opt/apache-cxf/lib/cxf-xjc-ts-2.4.0.jar')
sys.path.append('/opt/apache-cxf/lib/FastInfoset-1.2.9.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-activation_1.1_spec-1.1.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-annotation_1.0_spec-1.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-javamail_1.4_spec-1.7.1.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-jaxws_2.2_spec-1.0.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-jms_1.1_spec-1.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-servlet_3.0_spec-1.0.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-stax-api_1.0_spec-1.0.1.jar')
sys.path.append('/opt/apache-cxf/lib/geronimo-ws-metadata_2.0_spec-1.1.3.jar')
sys.path.append('/opt/apache-cxf/lib/isorelax-20030108.jar')
sys.path.append('/opt/apache-cxf/lib/jaxb-api-2.2.1.jar')
sys.path.append('/opt/apache-cxf/lib/jaxb-impl-2.2.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/jaxb-xjc-2.2.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/jettison-1.3.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-continuation-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-http-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-io-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-security-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-server-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/jetty-util-7.4.5.v20110725.jar')
sys.path.append('/opt/apache-cxf/lib/joda-time-1.6.2.jar')
sys.path.append('/opt/apache-cxf/lib/jra-1.0-alpha-4.jar')
sys.path.append('/opt/apache-cxf/lib/js-1.7R2.jar')
sys.path.append('/opt/apache-cxf/lib/jsr311-api-1.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/msv-core-2010.2.jar')
sys.path.append('/opt/apache-cxf/lib/neethi-3.0.1.jar')
sys.path.append('/opt/apache-cxf/lib/opensaml-2.4.1.jar')
sys.path.append('/opt/apache-cxf/lib/openws-1.4.1.jar')
sys.path.append('/opt/apache-cxf/lib/relaxngDatatype-20020414.jar')
sys.path.append('/opt/apache-cxf/lib/saaj-api-1.3.jar')
sys.path.append('/opt/apache-cxf/lib/saaj-impl-1.3.2.jar')
sys.path.append('/opt/apache-cxf/lib/serializer-2.7.1.jar')
sys.path.append('/opt/apache-cxf/lib/slf4j-api-1.6.1.jar')
sys.path.append('/opt/apache-cxf/lib/slf4j-jdk14-1.6.1.jar')
sys.path.append('/opt/apache-cxf/lib/spring-aop-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-asm-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-beans-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-context-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-core-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-expression-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-jms-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-tx-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/spring-web-3.0.5.RELEASE.jar')
sys.path.append('/opt/apache-cxf/lib/stax2-api-3.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/velocity-1.7.jar')
sys.path.append('/opt/apache-cxf/lib/woodstox-core-asl-4.1.1.jar')
sys.path.append('/opt/apache-cxf/lib/wsdl4j-1.6.2.jar')
sys.path.append('/opt/apache-cxf/lib/wss4j-1.6.2.jar')
sys.path.append('/opt/apache-cxf/lib/xalan-2.7.1.jar')
sys.path.append('/opt/apache-cxf/lib/xmlbeans-2.4.0.jar')
sys.path.append('/opt/apache-cxf/lib/xml-resolver-1.2.jar')
sys.path.append('/opt/apache-cxf/lib/xmlschema-core-2.0.jar')
sys.path.append('/opt/apache-cxf/lib/xmlsec-1.4.5.jar')
sys.path.append('/opt/apache-cxf/lib/xmltooling-1.3.1.jar')
sys.path.append('/opt/apache-cxf/lib/xsdlib-2010.1.jar')

#from nsi2 import *
import NSI2Interface

from java.lang import String
from java.util import ArrayList
import jarray

from reservation import Reservation

pNSA = 'urn:ogf:network:aist.go.jp:2013:nsa'
#pURI = 'https://163.220.30.173:22311/aist_upa/services/ConnectionProvider'
#pURI='http://127.0.0.1:28080/provider/services/ConnectionProvider'
#
# dummy NRM
# pURI='https://163.220.30.147:28443/provider/services/ConnectionProvider'
# dummy AG
# pURI='https://163.220.30.174:28443/provider/services/ConnectionProvider'
# real AG
pURI='https://163.220.30.174:28443/nsi2/services/ConnectionProvider'
# rNSA = 'urn:ogf:network:aist.go.jp:2013:nsa:felix'
rNSA = 'urn:ogf:network:aist.go.jp:2013:nsa'
rURI = 'https://163.220.30.145:29081/nsi2_requester/services/ConnectionRequester'
#rURI = 'https://127.0.0.1:29081/nsi2_requester/services/ConnectionRequester'
user = ''
password = ''

class NSI:
      def __init__(self):
            self.nsi = NSI2Interface(pNSA, pURI, rNSA, rURI, user, password)
            self.index = 1

      def reserve_sec(self, gid, src, dst, srcvlan, dstvlan, capacity, eros, start_sec, end_sec):
            rid = self.nsi.reserveCommit(gid, src, dst, srcvlan, dstvlan, capacity, start_sec, end_sec, eros)
            return rid

      def reserve(self, gid, sstp, dstp, svlantag, dvlantag, bw, 
                  ep_start, ep_end, eroEP):

            rid = self.nsi.reserveCommit(gid, sstp, dstp, svlantag, dvlantag,                                          bw, ep_start, ep_end, eroEP)
            self.index = self.index + 1
            logger.info("rid=%s" % (rid))
            return rid

      def modify_sec(self, gid, rid, end_sec):
            self.nsi.modifyCommit(gid, rid, end_sec)

      def modify(self, gid, rid, ep_end):
            mid = self.nsi.modifyCommit(gid, rid, ep_end)
            logger.info("mid=%s" % (mid))
            return mid

      def commit(self, rid):
            self.nsi.commit(rid)

      def abort(self, rid):
            self.nsi.abort(rid)

      def terminate(self, rid):
            self.nsi.terminate(rid)

      def provision(self, rid):
            self.nsi.provision(rid)

      def release(self, rid):
            self.nsi.release(rid)
            

if __name__ == "__main__":
      s_stp = "urn:ogf:network:aist.go.jp:2013:bi-ps"
      d_stp = "urn:ogf:network:aist.go.jp:2013:bi-aist-jgn-x"
      s_vlan = 1786
      d_vlan = s_vlan
      capacity = 100
      eros = ["urn:ogf:network:xxx:2013:stp1", "urn:ogf:network:yyy:2013:stp2"]
      gid = "TEST-GLOBAL-ID"
      nsi = NSI()

      epoch = datetime.utcfromtimestamp(0)
      start = datetime.utcnow()
      td = start - epoch
      
      start_sec = td.seconds + td.days * 24 * 3600
      end_sec = start_sec + 3600

      time.sleep(10)
      reservationId = nsi.reserve_sec(gid, s_stp, d_stp, s_vlan, d_vlan, capacity, eros, start_sec, end_sec)
      print reservationId

      time.sleep(10)
      nsi.modify_sec(gid, reservationId, end_sec)


      time.sleep(10)
      nsi.provision(reservationId)
      time.sleep(10)
      nsi.release(reservationId)
      time.sleep(10)
      nsi.terminate(reservationId)
      time.sleep(10)
      sys.exit()
      
