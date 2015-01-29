import sys
from datetime import datetime, timedelta
import time
import types

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

pNSA = 'urn:ogf:network:aist.go.jp:2013:nsa'
pURI = 'https://127.0.0.1:22311/aist_upa/services/ConnectionProvider'
rNSA = 'urn:ogf:network:aist.go.jp:2013:nsa'
rURI = 'https://127.0.0.1:29081/nsi2_requester/services/ConnectionRequester'
user = ''
password = ''

class NSI:
      def __init__(self):
            self.nsi = NSI2Interface(pNSA, pURI, rNSA, rURI, user, password)

      def reserve_sec(self, src, dst, srcvlan, dstvlan, capacity, eros, start_sec, end_sec):
            rid = self.nsi.reserveCommit(src, dst, srcvlan, dstvlan, capacity, start_sec, end_sec)
            return rid

      def reserve(self, resv):
            print "Enter reserve."
            ep_start = int(resv.start_time)
            ep_end = int(resv.end_time)
            print "start=%s" % (ep_start)
            print "end=%s" % (ep_end)

            rid = self.nsi.reserveCommit(resv.sSTP, resv.dSTP, int(resv.sEP.vlantag), int(resv.dEP.vlantag), int(resv.capacity), ep_start, ep_end)
            return rid

      def modify_sec(self, rid, end_sec):
            self.nsi.modifyCommit(rid, end_sec)

      def modify(self, rid, resv):
            ep_end = int(resv.end_time)
            print "end=%s" % (ep_end)

            self.nsi.modifyCommit(rid, ep_end)

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
      eros = {}
      nsi = NSI()

      epoch = datetime.utcfromtimestamp(0)
      start = datetime.utcnow()
      td = start - epoch
      
      start_sec = td.seconds + td.days * 24 * 3600
      end_sec = start_sec + 3600

      time.sleep(10)
      reservationId = nsi.reserve_sec(s_stp, d_stp, s_vlan, d_vlan, capacity, eros, start_sec, end_sec)
      print reservationId

      time.sleep(10)
      nsi.modify_sec(reservationId, end_sec)


      time.sleep(10)
      nsi.provision(reservationId)
      time.sleep(10)
      nsi.release(reservationId)
      time.sleep(10)
      nsi.terminate(reservationId)
      time.sleep(10)
      sys.exit()
      
