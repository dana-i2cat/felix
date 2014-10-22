from commons_tn import Link


# SE Data Models
class SELink(Link):
    def __init__(self, component_id, typee, component_manager_name=None,
                 vlantag=None, sliver=None):
        super(SELink, self).__init__(component_id, component_manager_name,
                                     vlantag=vlantag)
        self.link['link_type'] = typee
        self.link['sliver_id'] = sliver
