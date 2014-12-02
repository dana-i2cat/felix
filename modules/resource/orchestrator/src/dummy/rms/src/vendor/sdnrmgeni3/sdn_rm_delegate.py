import amsoil.core.pluginmanager as pm
import amsoil.core.log
import datetime
logger = amsoil.core.log.getLogger('sdnrmgeniv3delegate')

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')
rspec_manager = pm.getService('geni3RSpecsManager')


class SDNRMGENI3Delegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:SDNRM_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/ext/openflow/3'

    def __init__(self):
        super(SDNRMGENI3Delegate, self).__init__()
        logger.info("SDNRMGENI3Delegate successfully initialized!")

    def enter_method_log(f):
        as_ = f.func_code.co_varnames[:f.func_code.co_argcount]

        def wrapper(*args, **kwargs):
            ass_ = ', '.join('%s=%r' % e for e in zip(as_, args) +
                             kwargs.items())
            logger.info("Calling %s with args=%s" % (f.func_name, ass_,))
            return f(*args, **kwargs)
        return wrapper

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        request.xsd"""
        return {'sdnrm': 'http://example.com/sdnrm'}

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        manifest.xsd"""
        return {'openflow': self.MANIFEST_URL}

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        ad.xsd"""
        return {'sdnrm': 'http://example.com/sdnrm'}

    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers."""
        return 'geni_many'

    def __create_of_datapath(self, prefix, dpid):
        dpath = rspec_manager.get_Datapath(prefix + "datapath+" + dpid,
                                           prefix + "cm", dpid)
        for i in range(1, 17):
            dpath.add_port(i, "GBE0/%d" % (i))
        return dpath

    def __create_of_link(self, prefix, d1, p1, d2, p2):
        link = rspec_manager.get_OFLink(prefix + "link+%s_%d_%s_%d" %
                                      (d1, p1, d2, p2))
        link.add_datapath(rspec_manager.get_Datapath(
            prefix + "datapath+" + d1, prefix + "cm", d1).serialize())
        link.add_port(p1)
        link.add_datapath(rspec_manager.get_Datapath(
            prefix + "datapath+" + d2, prefix + "cm", d2).serialize())
        link.add_port(p2)
        return link

    def __create_fed_link(self, prefix, fprefix, name, d1, p1, d2, p2):
        link = rspec_manager.get_FEDLink(prefix + "link+%s_%s_%s_%s" %
                                         (d1, p1, d2, p2))
        link.set_link_type(name)
        link.set_component_manager(fprefix + "cm")
        link.add_interface_id(fprefix + "device+" + d1 + "_" + p1)
        link.add_interface_id(fprefix + "device+" + d2 + "_" + p2)
        return link

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec = rspec_manager.get_OFv3AdvertisementFormatter()
        prefix = "urn:publicid:IDN+openflow:i2cat.ofam+"
        # datapath 1
        of_dpath = self.__create_of_datapath(prefix, "00:10:00:00:00:00:00:05")
        rspec.datapath(of_dpath.serialize())
        # datapath 2
        of_dpath = self.__create_of_datapath(prefix, "00:10:00:00:00:00:00:03")
        rspec.datapath(of_dpath.serialize())
        # datapath 3
        of_dpath = self.__create_of_datapath(prefix, "00:10:00:00:00:00:00:04")
        rspec.datapath(of_dpath.serialize())
        # datapath 4
        of_dpath = self.__create_of_datapath(prefix, "00:10:00:00:00:00:00:01")
        rspec.datapath(of_dpath.serialize())
        # datapath 5
        of_dpath = self.__create_of_datapath(prefix, "00:10:00:00:00:00:00:02")
        rspec.datapath(of_dpath.serialize())
        # oflink 1
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:03", 2,
                                     "00:10:00:00:00:00:00:02", 3)
        rspec.of_link(link.serialize())
        # oflink 2
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:02", 5,
                                     "00:10:00:00:00:00:00:05", 2)
        rspec.of_link(link.serialize())
        # oflink 3
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:03", 4,
                                     "00:10:00:00:00:00:00:04", 3)
        rspec.of_link(link.serialize())
        # oflink 4
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:03", 1,
                                     "00:10:00:00:00:00:00:01", 3)
        rspec.of_link(link.serialize())
        # oflink 5
        link = self.__create_of_link(prefix, "05:00:00:00:00:00:00:03", 7,
                                     "00:10:00:00:00:00:00:03", 9)
        rspec.of_link(link.serialize())
        # oflink 6
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:01", 4,
                                     "00:10:00:00:00:00:00:04", 1)
        rspec.of_link(link.serialize())
        # oflink 7
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:04", 2,
                                     "00:10:00:00:00:00:00:02", 4)
        rspec.of_link(link.serialize())
        # oflink 8
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:04", 1,
                                     "00:10:00:00:00:00:00:01", 4)
        rspec.of_link(link.serialize())
        # oflink 9
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:01", 3,
                                     "00:10:00:00:00:00:00:03", 1)
        rspec.of_link(link.serialize())
        # oflink 10
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:04", 5,
                                     "00:10:00:00:00:00:00:05", 4)
        rspec.of_link(link.serialize())
        # oflink 11
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:04", 3,
                                     "00:10:00:00:00:00:00:03", 4)
        rspec.of_link(link.serialize())
        # oflink 12
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:05", 1,
                                     "00:10:00:00:00:00:00:01", 5)
        rspec.of_link(link.serialize())
        # oflink 13
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:03", 5,
                                     "00:10:00:00:00:00:00:05", 3)
        rspec.of_link(link.serialize())
        # oflink 14
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:01", 2,
                                     "00:10:00:00:00:00:00:02", 1)
        rspec.of_link(link.serialize())
        # oflink 15
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:05", 3,
                                     "00:10:00:00:00:00:00:03", 5)
        rspec.of_link(link.serialize())
        # oflink 16
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:02", 4,
                                     "00:10:00:00:00:00:00:04", 2)
        rspec.of_link(link.serialize())
        # oflink 17
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:05", 2,
                                     "00:10:00:00:00:00:00:02", 5)
        rspec.of_link(link.serialize())
        # oflink 18
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:05", 4,
                                     "00:10:00:00:00:00:00:04", 5)
        rspec.of_link(link.serialize())
        # oflink 19
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:02", 1,
                                     "00:10:00:00:00:00:00:01", 2)
        rspec.of_link(link.serialize())
        # oflink 20
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:02", 3,
                                     "00:10:00:00:00:00:00:03", 2)
        rspec.of_link(link.serialize())
        # oflink 21
        link = self.__create_of_link(prefix, "00:10:00:00:00:00:00:01", 5,
                                     "00:10:00:00:00:00:00:05", 1)
        rspec.of_link(link.serialize())
        # fedlink 1
        fed_prefix = "urn:publicid:IDN+federation:i2cat.ofam+"
        link = self.__create_fed_link(prefix, fed_prefix,
                                      "Federation_i2cat-VirtualWall-A",
                                      "00:10:00:00:00:00:00:03", "10",
                                      "VirtualWall-GW-A", "")
        rspec.fed_link(link.serialize())
        # fedlink 2
        link = self.__create_fed_link(prefix, fed_prefix,
                                      "Federation_i2cat-VirtualWall-B",
                                      "00:10:00:00:00:00:00:03", "11",
                                      "VirtualWall-GW-B", "")
        rspec.fed_link(link.serialize())
        # fedlink 3
        link = self.__create_fed_link(prefix, fed_prefix,
                                      "Federation_i2cat-VirtualWall-C",
                                      "00:10:00:00:00:00:00:04", "10",
                                      "VirtualWall-GW-C", "")
        rspec.fed_link(link.serialize())
        # fedlink 4
        link = self.__create_fed_link(prefix, fed_prefix,
                                      "Federation_i2cat-VirtualWall-D",
                                      "00:10:00:00:00:00:00:04", "11",
                                      "VirtualWall-GW-D", "")
        rspec.fed_link(link.serialize())
        logger.debug("OFv3AdvertisementFormatter=%s" % (rspec,))
        (result, error) = rspec_manager.call_validate(rspec.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))

        logger.info("list-resources success!")
        return "%s" % rspec

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    def __test_urns(self, urns, offset):
        values, last_urn = [], ""
        for urn in urns:
            if self.urn_type(urn) == "slice":
                last_urn = urn

        values = [{"id": "sdn-dpid_%d" % (i)} for i in range(0, offset)]
        return values, last_urn

    def __test_datapaths(self, dpids):
        if len(dpids) == 0:
            raise geni_ex.GENIv3SearchFailedError(
                "No resources in the given slice-urns")

    @enter_method_log
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 4)
        self.__test_datapaths(datapaths)

        sliver = {"description": "test describe geniv3 method",
                  "ref": "geni site",
                  "email": "r.monno@nextworks.it"}

        slivers = [self.__sliver_str_status(d) for d in datapaths]
        manifest = self.lxml_to_string(self.__manifest(sliver))

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {'geni_rspec': manifest,
                'geni_urn': last_slice_urn,
                'geni_slivers': slivers}

    def __sliver_str_status(self, dpid):
        return {'geni_sliver_urn': dpid.get("id"),
                'geni_expires': self.__datetime2str(datetime.datetime.now()),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': ""}

    def __sliver_date_status(self, dpid, etime=None):
        t = datetime.datetime.now() if (etime is None) else etime
        return {'geni_sliver_urn': dpid.get("id"),
                'geni_expires': t,
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': ""}

    def __sliver_details_status(self, dpid):
        cid = dpid.get("id")
        return {'geni_sliver_urn': cid,
                'geni_expires': datetime.datetime.now(),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': "",
                'geni_resource_status': "some-details-%s" % cid}

    def __manifest(self, sliver):
        mr = self.lxml_manifest_root()
        em = self.lxml_manifest_element_maker('openflow')

        ref = "Pending" if sliver.get("ref") is None else sliver.get("ref")

        s = em.sliver(email=sliver.get("email"),
                      description=sliver.get("description"),
                      ref=ref)
        mr.append(s)

        return mr

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec_ = rspec_manager.get_OFv3RequestParser(from_string=rspec)
        logger.debug("OFv3RequestParser=%s" % (rspec_,))
        (result, error) = rspec_manager.call_validate(rspec_.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))

        logger.info("Validation success!")
        sliver = rspec_.sliver()
        logger.info("Sliver=%s" % sliver)

        controllers = rspec_.controllers()
        logger.info("Controllers=%s" % controllers)

        groups = rspec_.groups()
        logger.info("Groups=%s" % groups)

        datapaths = []
        for g in groups:
            dpids = rspec_.datapaths(g.get("name"))
            logger.info("Group=%s, Datapaths=%s" % (g.get("name"), dpids))
            datapaths.extend(dpids)

        matches = rspec_.matches()
        logger.info("Matches=%s" % matches)

        slivers = [self.__sliver_date_status(d) for d in datapaths]
        manifest = self.lxml_to_string(self.__manifest(sliver))

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return (manifest, slivers)

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 5)
        self.__test_datapaths(datapaths)

        slivers = [self.__sliver_date_status(d, expiration_time)
                   for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def provision(self, urns, client_cert, credentials, best_effort, end_time,
                  geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")

    @enter_method_log
    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 3)
        self.__test_datapaths(datapaths)

        slivers = [self.__sliver_date_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return "test-status-slice_urn", slivers

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        datapaths, last_slice_urn = self.__test_urns(urns, 9)
        self.__test_datapaths(datapaths)

        slivers = [self.__sliver_details_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 6)
        self.__test_datapaths(datapaths)

        slivers = [self.__sliver_date_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")
