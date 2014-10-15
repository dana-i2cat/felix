from commons_tn import Link


# SE Data Models
class SELink(Link):
    def __init__(self, component_id, component_manager_name, typee):
        super(SELink, self).__init__(component_id, component_manager_name)
        self.link['link_type'] = typee
