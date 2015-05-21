import xmlrpclib
import yaml
import os

print "POX plugin loaded"

current_path = os.path.dirname(os.path.abspath( __file__ ))
conf_file_path = os.path.join(current_path, "../../../../conf/pox-config.yaml")
stream = open(conf_file_path, "r")
config = yaml.load(stream)

host = str(config["host"])
port = str(config["rest_port"])


class i2catClient:

    SERVER_URL = "http://" + host + ":" + port
    
    def __init__(self):
        self.__channel = xmlrpclib.ServerProxy(self.SERVER_URL)
        

    def add_rule(self, src_port, src_vlan, dst_port, dst_vlan):
        """ Retrieves the SRC and DST ports of the HP switch,
            the SRC (FlowSpace) and DST (Transport) Vlans and
            sets up a bi-directional circuit to link two islands 
            by calling the NorthBound API of the i2CAT POX 
            Controller  
        """
        return self.__channel.add_rule(src_port, src_vlan, dst_port, dst_vlan)

    def remove_rule(self, src_port, src_vlan, dst_port, dst_vlan):
       """ Retrieves the SRC and DST ports of the HP switch,
           the SRC (FlowSpace) and DST (Transport) Vlans and
           deletes the previously provisioned bi-directional 
           circuit linking two islands by calling the NorthBound 
           API of the i2CAT POX Controller  
       """
       return self.__channel.remove_rule(src_port, src_vlan, dst_port, dst_vlan)

    def configure_vlan(self, *args, **kwargs):
       """ Retrieves a transport VLAN and configures
           the i2cat HP ProCurve Switch to work as 
           aggreggate openflow instance 
       """
       pass

PoxController = i2catClient()

def addSwitchingRule(in_port, out_port, in_vlan, out_vlan):
    """
    params: in_port (int)
            out_port (int)
            in_vlan (int)
            out_vlan (int)
    """
    print "install flows"
    response = PoxController.add_rule(int(in_port), int(in_vlan), int(out_port), int(out_vlan))
    response = PoxController.add_rule(int(out_port), int(out_vlan), int(in_port), int(in_vlan))
    print response

def deleteSwitchingRule(in_port, out_port, in_vlan, out_vlan):
    """
    params: in_port (int)
            out_port (int)
            in_vlan (int)
            out_vlan (int)
    """
    print "delete flows"
    response = PoxController.remove_rule(int(in_port), int(in_vlan), int(out_port), int(out_vlan))
    response = PoxController.remove_rule(int(out_port), int(out_vlan), int(in_port), int(in_vlan))
    print response
