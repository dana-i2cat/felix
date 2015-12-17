from commons import CommonUtils

import core
logger = core.log.getLogger("vl-utils")


class VLUtils(CommonUtils):
    def __init__(self):
        super(VLUtils, self).__init__()

    def get_domains_from_link(self, link):
        src_dom = ""
        dst_dom = ""
        try:
            src_dom = self.get_domain_from_urn(link["interface_ref"][0]["component_id"])
            dst_dom = self.get_domain_from_urn(link["interface_ref"][1]["component_id"])
        except:
             logger.warning("Some interface of virtual link is invalid.\n" \
                 + "Virtual-link=%s. Details: %s" % (link, str(e)))
        return (src_dom, dst_dom)

    @staticmethod
    def get_type_from_link(link):
        link_type = ""
        link = link["link_type"].split("+type+")
        if len(link) == 2:
            link_type = link[1]
        return link_type

    @staticmethod
    def get_domain_from_urn(urn):
        domain = ""
        index = urn.rfind("+")
        domain = urn[index+1:]
        return domain
