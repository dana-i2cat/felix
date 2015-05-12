from delegate.geni.v3.rspecs.tnrm.request_parser import TNRMv3RequestParser
from delegate.geni.v3.rspecs.commons_se import SELink


class SERMv3RequestParser(TNRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3RequestParser, self).__init__(from_file, from_string)

    def links(self):
        links_ = []
        for l in self.rspec.findall(".//{%s}link" % (self.none)):
            manager_ = l.find("{%s}component_manager" % (self.none))
            if manager_ is None:
                self.raise_exception("Component-Mgr tag not found in link!")

            type_ = l.find("{%s}link_type" % (self.none))
            if type_ is None:
                self.raise_exception("Link-Type tag not found in link!")

            l_ = SELink(l.attrib.get("client_id"), type_.attrib.get("name"),
                        manager_.attrib.get("name"))

            [l_.add_interface_ref(i.attrib.get("client_id"))
             for i in l.iterfind("{%s}interface_ref" % (self.none))]

            [l_.add_property(p.attrib.get("source_id"),
                             p.attrib.get("dest_id"),
                             p.attrib.get("capacity"))
             for p in l.iterfind("{%s}property" % (self.none))]

            links_.append(l_.serialize())

        return links_

    def getVlanPairs(self):
        try:
            sliceVlanPairs=[]
            for l in self.rspec.findall(".//{%s}link" % (self.none)):
                client_id = l.attrib["client_id"]
                vlanPairs=[]
                vlanPairs.append(client_id)
                for i in l.iterfind("{%s}interface_ref" % (self.none)):
                    singleVlanPair={}
                    singleVlanPair["vlan"] = i.attrib["{http://ict-felix.eu/serm_request}vlan"] # felix:vlan param
                    # singleVlanPair["port_id"] = i.attrib["client_id"].split("_")[-1]
                    singleVlanPair["port_id"] = i.attrib["client_id"]
                    vlanPairs.append(singleVlanPair)
                sliceVlanPairs.append(vlanPairs)
            return sliceVlanPairs
        except:
            try:
                sliceVlanPairs=[]
                for l in self.rspec.findall(".//{%s}link" % (self.none)):
                    client_id = l.attrib["client_id"]
                    vlanPairs=[]
                    vlanPairs.append(client_id)
                    
                    for i in l.iterfind("{%s}interface_ref" % (self.none)):
                        singleVlanPair={}
                        port_id = i.attrib["client_id"]
                        singleVlanPair["port_id"] = port_id

                        for n in self.rspec.findall(".//{%s}node" % (self.none)):
                            for i in n.findall(".//{%s}interface[@client_id='%s']" % (self.none, port_id)):
                                vlan_element = i.find(".//{http://www.geni.net/resources/rspec/ext/shared-vlan/1}link_shared_vlan")
                                singleVlanPair["vlan"] = vlan_element.attrib["vlantag"]
                                vlanPairs.append(singleVlanPair)                

                    # for i in l.iterfind("{%s}interface_ref" % (self.none)):
                    #     singleVlanPair={}
                    #     singleVlanPair["vlan"] = i.attrib["{http://ict-felix.eu/serm_request}vlan"] # felix:vlan param
                    #     # singleVlanPair["port_id"] = i.attrib["client_id"].split("_")[-1]
                    #     singleVlanPair["port_id"] = i.attrib["client_id"]
                    #     vlanPairs.append(singleVlanPair)
                    sliceVlanPairs.append(vlanPairs)
                return sliceVlanPairs

            except:
                return None
