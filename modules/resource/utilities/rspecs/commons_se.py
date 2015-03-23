from commons_tn import Link, Node


# SE Data Models
class SENode(Node):
    def __init__(self, component_id, component_manager_id, exclusive=None,
                 sliver_type_name=None, component_manager_uuid=None,
                 hostname=None):
        super(SENode, self).__init__(component_id, component_manager_id,
                                     exclusive, sliver_type_name,
                                     component_manager_uuid)
        self.node['host_name'] = hostname


class SELink(Link):
    def __init__(self, component_id, typee, component_manager_name=None,
                 vlantag=None, sliver=None):
        super(SELink, self).__init__(component_id, component_manager_name,
                                     vlantag=vlantag)
        self.link['link_type'] = typee
        self.link['sliver_id'] = sliver
