from lxml import etree
import core

logger = core.log.getLogger("monitoring-utils")


class MonitoringUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def check_existing_tag_in_topology(root, node, node_type, node_urns, domain=None):
        tag_exists = False
        try:
            elements = []
            if not isinstance(node_urns, list):
                node_urns = [ node_urns ]
            try:
                for node_urn in node_urns:
                    if node == "link":
                        interfaces_same_link = True
                        elem = root.xpath("//%s[@type='%s']//interface_ref[@client_id='%s']" % (node, node_type, node_urn))
                        if node_type == None:
                            elem = root.xpath("//%s//interface_ref[@client_id='%s']" % (node, node_urn))
                        for element in elements:
                            if element.getparent() == elem[0].getparent():
                                interfaces_same_link &= True
                            else:
                                interfaces_same_link &= False
                        if interfaces_same_link:
                            elements.extend(elem)
                    else:
                        if node_type == "tn":
                            if domain is not None:
                                domain = domain if "urn" in domain else "urn:publicid:IDN+ocf:" + domain
                                if node_type == None:
                                    elements = root.xpath("//topology[@name='%s']//%s[@id='%s']" % (domain, node, node_urn))
                                elements = root.xpath("//topology[@name='%s']//%s[@type='%s'][@id='%s']" % (domain, node, node_type, node_urn))
                        else:
                            elements = root.xpath("//%s[@type='%s'][@id='%s']" % (node, node_type, node_urn))
                            if node_type == None:
                                elements = root.xpath("//%s[@id='%s']" % (node, node_urn))
            except Exception:
                pass
            if len(elements) > 0:
                tag_exists = True
        except:
            pass
        return tag_exists
