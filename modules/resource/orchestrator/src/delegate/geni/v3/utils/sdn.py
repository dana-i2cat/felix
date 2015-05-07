from delegate.geni.v3.rm_adaptor import AdaptorFactory
from rspecs.openflow.manifest_parser import OFv3ManifestParser
from rspecs.openflow.request_formatter import OFv3RequestFormatter
from rspecs.commons_of import Match
from db.db_manager import db_sync_manager
from commons import CommonUtils

import core
logger = core.log.getLogger("sdn-utils")


class SDNUtils(CommonUtils):
    def __init__(self):
        super(SDNUtils, self).__init__()

    def manage_describe(self, peer, urns, creds):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn, ss = adaptor.describe(urns, creds[0]["geni_value"])

            manifest = OFv3ManifestParser(from_string=m)
            logger.debug("OFv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            slivers = manifest.slivers()
            logger.info("Slivers(%d)=%s" % (len(slivers), slivers,))

            return ({"slivers": slivers}, urn, ss)
        except Exception as e:
            logger.critical("manage_describe exception: %s", e)
            raise e

    def manage_provision(self, peer, urns, creds, beffort, etime, gusers):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            m, urn = adaptor.provision(
                urns, creds[0]["geni_value"], beffort, etime, gusers)

            manifest = OFv3ManifestParser(from_string=m)
            logger.debug("OFv3ManifestParser=%s" % (manifest,))
            self.validate_rspec(manifest.get_rspec())

            slivers = manifest.slivers()
            logger.info("Slivers(%d)=%s" % (len(slivers), slivers,))

            return ({"slivers": slivers}, urn)
        except Exception as e:
            # It is possible that SDNRM does not implement this method!
            if beffort:
                logger.error("manage_provision exception: %s", e)
                return ({"slivers": []}, [])
            else:
                logger.critical("manage_provision exception: %s", e)
                raise e

    def __update_route(self, route, values):
        for v in values:
            for dpid in v.get("dpids"):
                k = db_sync_manager.get_sdn_datapath_routing_key(dpid)
                dpid["routing_key"] = k
                if k not in route:
                    route[k] = OFv3RequestFormatter()

    def __create_se_id(self, component_id, port_name):
        return component_id + ":" + port_name

    def __extract_se_from_sdn(self, groups, matches):
        ret = []
        for m in matches:
            vlan_id = m.get("packet").get("dl_vlan")
            if vlan_id is None:
                continue

            dpids = []
            for mg in m.get("use_groups"):
                for g in groups:
                    if g.get("name") == mg.get("name"):
                        for gds in g.get("dpids"):
                            for p in gds.get("ports"):
                                seid = self.__create_se_id(
                                    gds.get("component_id"), p.get("name"))
                                dpids.append(seid)

            for mds in m.get("dpids"):
                for p in mds.get("ports"):
                    seid = self.__create_se_id(
                        mds.get("component_id"), p.get("name"))
                    dpids.append(seid)

            if len(dpids) > 0:
                ret.append({"vlan": vlan_id, "dpids": dpids})

        return ret

    def __update_route_rspec(self, route, sliver, controllers, groups,
                             matches):
        for key, rspec in route.iteritems():
            rspec.sliver(sliver.get("description"), sliver.get("ref"),
                         sliver.get("email"))
            for c in controllers:
                rspec.controller(c.get("url"), c.get("type"))
            for g in groups:
                rspec.group(g.get("name"))
                for dpid in g.get("dpids"):
                    if dpid.get("routing_key") == key:
                        rspec.group_datapath(g.get("name"), dpid)
            for m in matches:
                match = Match()
                for uf in m.get("use_groups"):
                    match.add_use_group(uf.get("name"))
                for dpid in m.get("dpids"):
                    if dpid.get("routing_key") == key:
                        match.add_datapath(dpid)
                match.set_packet(m.get("packet").get("dl_src"),
                                 m.get("packet").get("dl_dst"),
                                 m.get("packet").get("dl_type"),
                                 m.get("packet").get("dl_vlan"),
                                 m.get("packet").get("nw_src"),
                                 m.get("packet").get("nw_dst"),
                                 m.get("packet").get("nw_proto"),
                                 m.get("packet").get("tp_src"),
                                 m.get("packet").get("tp_dst"))
                rspec.match(match.serialize())

    def manage_allocate(self, surn, creds, end, sliver, parser, slice_urn):
        route = {}
        controllers = parser.of_controllers()
        logger.debug("Controllers=%s" % (controllers,))

        groups = parser.of_groups()
        self.__update_route(route, groups)
        logger.debug("Groups=%s" % (groups,))

        matches = parser.of_matches()
        self.__update_route(route, matches)
        logger.debug("Matches=%s" % (matches,))

        se_sdn_info = self.__extract_se_from_sdn(groups, matches)
        logger.debug("SE-SDN-INFO=%s" % (se_sdn_info,))

        self.__update_route_rspec(route, sliver, controllers, groups, matches)
        logger.info("Route=%s" % (route,))
        manifests, slivers, db_slivers = [], [], []

        for k, v in route.iteritems():
            try:
                (m, ss) =\
                    self.send_request_allocate_rspec(k, v, surn, creds, end)
                manifest = OFv3ManifestParser(from_string=m)
                logger.debug("OFv3ManifestParser=%s" % (manifest,))

                slivers_ = manifest.slivers()
                logger.info("Slivers(%d)=%s" % (len(slivers_), slivers_,))
                manifests.append({"slivers": slivers_})

                self.extend_slivers(ss, k, slivers, db_slivers)
            except Exception as e:
                logger.critical("manage_sdn_allocate exception: %s", e)
                raise e

        # insert sliver details (groups and matches) into the slice.sdn table
        id_ = db_sync_manager.store_slice_sdn(slice_urn, groups, matches)
        logger.info("Stored slice.sdn info: id=%s" % (id_,))

        return (manifests, slivers, db_slivers, se_sdn_info)
