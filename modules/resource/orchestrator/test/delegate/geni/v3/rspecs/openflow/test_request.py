import sys
# Adding paths to locate modules within the "src" package
sys.path.insert(0, "../../../../../../src")
from delegate.geni.v3.rspecs.openflow.commons import Datapath, Match, CONTROLLER_TYPE_PRIMARY
from delegate.geni.v3.rspecs.openflow.request_formatter import OFv3RequestFormatter
from delegate.geni.v3.rspecs.openflow.request_parser import OFv3RequestParser
# Adding path to locate "utils" module within the "test" package
sys.path.insert(0, "../../../../../..")
from test.delegate.geni.v3.rspecs.utils import rspec_validation
from test.utils import testcase


class TestRequest(testcase.TestCase):
    @classmethod
    def setUp(self):
        """
        Sets up environment, e.g. asking for credentials.
        """
        self.rspec = OFv3RequestFormatter()
        self.rspec.sliver(description="My GENI experiment",
                     ref="http://www.geni.net",
                     email="user@geni.net")
        self.rspec.controller(url="tcp:myctrl.example.net:9933",
                         type=CONTROLLER_TYPE_PRIMARY)
        self.rspec.group(name="mygrp")
    
        # first datapath
        prefix = "urn:publicid:IDN+openflow:foam:uxmal.gpolab.bbn.com+"
        dp = Datapath(prefix + "datapath:06:a4:00:12:e2:b8:a5:d0",
                      prefix + "authority+am",
                      "06:a4:00:12:e2:b8:a5:d0")
        dp.add_port(7, "GBE0/7")
        dp.add_port(20, "GBE0/20")
        self.rspec.datapath("mygrp", dp)
    
        # second datapath
        dp = Datapath(prefix + "datapath:06:af:00:24:a8:c4:b9:00",
                      prefix + "authority+am",
                      "06:af:00:24:a8:c4:b9:00")
        dp.add_port(50, "26")
        dp.add_port(71, "47")
        dp.add_port(65534)
        self.rspec.datapath("mygrp", dp)
    
        # first match
        m = Match()
        m.add_use_group("mygrp")
        m.add_use_group("pippuzzo")
        m.set_packet(dl_type="0x800", nw_src="10.1.1.0/24",
                     nw_proto="6, 17", tp_src="80")
        self.rspec.match(m)
    
        # second match
        m = Match()
        m.add_use_group("mygrp")
        m.add_datapath(dp)
        m.add_datapath(dp)
        m.set_packet(dl_type="0x800", nw_dst="10.1.1.0/24",
                     nw_proto="617", tp_dst="8080")
        self.rspec.match(m)
    
    def tearDown(self):
        pass
    
    def test_validate(self):
        (result, error) = rspec_validation.validate(self.rspec.get_rspec())
        self.assertEquals(True, result)

if __name__ == '__main__':
    # Allows to run in stand-alone mode
    testcase.main()
