from commons import CommonUtils
from core import organisations
from mapper.path_finder_tn_to_sdn import PathFinderTNtoSDN

import core
logger = core.log.getLogger("vl-utils")
import itertools


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

    @staticmethod
    def find_vlinks_from_tn_stps(tn_utils):
        orgs = organisations.AllowedOrganisations.get_organisations_type()
        combined_orgs = itertools.combinations(orgs, 2)
        links = []
        for combined in combined_orgs:
            link = {}
            paths = PathFinderTNtoSDN(combined[0], combined[1]).find_paths()
            for path in paths:
                src_tn = path["src"]["tn"]
                dst_tn = path["dst"]["tn"]
                is_gre = all(tn_utils.determine_stp_gre([src_tn, dst_tn]))
                link_type = "gre" if is_gre else "nsi"
                vl_base_urn = "urn:publicid:IDN+fms:{0}:mapper+domain".format(combined[0])
                src_urn = "%s+%s" % (vl_base_urn, combined[0])
                dst_urn = "%s+%s" % (vl_base_urn, combined[1])
                link = {"src_name": src_urn,
                        "dst_name": dst_urn,
                        "link_type": link_type}
                if link not in links:
                    links.append(link)
        return links
