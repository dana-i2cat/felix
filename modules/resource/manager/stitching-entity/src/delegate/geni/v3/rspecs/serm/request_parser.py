from delegate.geni.v3.rspecs.tnrm.request_parser import TNRMv3RequestParser
from delegate.geni.v3.rspecs.commons_se import SELink
from delegate.geni.v3.rspecs.commons_tn import Node, Interface
import delegate.geni.v3.se_static_links_manager as SEStaticLinkManager


class SERMv3RequestParser(TNRMv3RequestParser):
    def __init__(self, from_file=None, from_string=None):
        super(SERMv3RequestParser, self).__init__(from_file, from_string)
        self.checkStaticLinksInRspec()
        self.SEStaticLinkManager = SEStaticLinkManager.StaticLinkVlanManager()
        print "GGGGGGGGGG:\n" + from_string + "\nGGGGGGGGG"
        self.__sv = self.rspec.nsmap.get('sharedvlan')

    def checkStaticLinksInRspec(self):
        print ">>> Checking static links"
        # for l in self.rspec.findall(".//{%s}link" % (self.none)):
        #     client_id = l.attrib["client_id"]
        #     vlanPairs=[]
        #     vlanPairs.append(client_id)
        #     for i in l.iterfind("{%s}interface_ref" % (self.none)):
        #         singleVlanPair={}
        #         singleVlanPair["vlan"] = i.attrib["{http://ict-felix.eu/serm_request}vlan"] # felix:vlan param

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

    def nodes(self):
        nodes_ = []
        for n in self.rspec.findall(".//{%s}node" % (self.none)):
            s_ = None
            sliver_ = n.find("{%s}sliver_type" % (self.none))
            if sliver_ is not None:
                s_ = sliver_.attrib.get("name")

            n_ = Node(n.attrib.get("client_id"),
                      n.attrib.get("component_manager_id"),
                      n.attrib.get("exclusive"), s_)

            for i in n.iterfind("{%s}interface" % (self.none)):
                i_ = Interface(i.attrib.get("client_id"))
                for sv in i.iterfind("{%s}link_shared_vlan" % (self.__sv)):
                    if sv.attrib.get("vlantag") == "0":
                        staticPort = i.attrib.get("client_id").split("_")[-1]
                        staticPortVlan = self.SEStaticLinkManager.chooseVlan(staticPort)
                        i_.add_vlan(staticPortVlan,
                                    sv.attrib.get("name"))
                    else:
                        i_.add_vlan(sv.attrib.get("vlantag"),
                                    sv.attrib.get("name"))
                n_.add_interface(i_.serialize())

            nodes_.append(n_.serialize())

        return nodes_

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
