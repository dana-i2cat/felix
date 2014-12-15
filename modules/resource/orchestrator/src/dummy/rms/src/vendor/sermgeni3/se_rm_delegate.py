import amsoil.core.pluginmanager as pm
import amsoil.core.log
import datetime
logger = amsoil.core.log.getLogger('sermgeniv3delegate')

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')
rspec_manager = pm.getService('geni3RSpecsManager')


class SERMGENI3Delegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:SERM_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/ext/se/3'

    def __init__(self):
        super(SERMGENI3Delegate, self).__init__()
        self.RM_URN = "urn:publicid:IDN+stitching:psnc.serm"
        logger.info("SERMGENI3Delegate successfully initialized!")

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
        return {'se': self.MANIFEST_URL}

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

    def __create_se_dyn_link(self, lid, cmid, typee, id1, id2, cap=None):
        l = rspec_manager.get_SELink(lid, typee, cmid)
        l.add_interface_ref(id1)
        l.add_interface_ref(id2)
        if cap is not None:
            l.add_property(id1, id2, cap)
            l.add_property(id2, id1, cap)
        return l

    def __create_se_stat_link(self, lid, typee, id1, id2):
        l = rspec_manager.get_SELink(lid, typee)
        l.add_interface_ref(id1)
        l.add_interface_ref(id2)
        return l

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec = rspec_manager.get_SERMv3AdvertisementFormatter()
        # node = domain
        node = rspec_manager.get_TNNode(self.RM_URN,
                                      self.RM_URN + "+authority+serm",
                                      "false")
        # if-1
        intf = rspec_manager.get_Interface(self.RM_URN + "+interface+if1")
        node.add_interface(intf.serialize())
        # if-2
        intf = rspec_manager.get_Interface(self.RM_URN + "+interface+if2")
        node.add_interface(intf.serialize())
        # if-3
        intf = rspec_manager.get_Interface(self.RM_URN + "+interface+if3")
        node.add_interface(intf.serialize())
        # if-4
        intf = rspec_manager.get_Interface(self.RM_URN + "+interface+if4")
        node.add_interface(intf.serialize())

        rspec.node(node.serialize())

        # link 1
        link = self.__create_se_dyn_link(self.RM_URN + "+link+dyn1",
                                         self.RM_URN "+authority+serm",
                                         "urn:felix+vlan_trans",
                                         "*", "*", "1G")
        rspec.link(link.serialize())
        # link 2
        link = self.__create_se_stat_link(self.RM_URN + "+link+se1-dp1",
                                          "urn:felix+static_link",
                                          self.RM_URN + "+interface+if1",
                                          "urn:publicid:IDN+openflow:i2cat.ofam+datapath+00:10:00:00:00:00:00:01")
        rspec.link(link.serialize())
        # link 3
        link = self.__create_se_stat_link(self.RM_URN + "+link+se1-dp2",
                                          "urn:felix+static_link",
                                          self.RM_URN + "+interface+if2",
                                          "urn:publicid:IDN+openflow:i2cat.ofam+datapath+00:10:00:00:00:00:00:02")
        rspec.link(link.serialize())
        # link 4
        link = self.__create_se_stat_link(self.RM_URN + "+link+se1-dp3",
                                          "urn:felix+static_link",
                                          self.RM_URN + "+interface+if3",
                                          self.RM_URN + "+link+stp1")
        rspec.link(link.serialize())
        # link 5
        link = self.__create_se_stat_link(self.RM_URN + "+link+se1-dp4",
                                          "urn:felix:static_link",
                                          self.RM_URN + "+interface+if4",
                                          self.RM_URN + "+link+stp2")
        rspec.link(link.serialize())

        logger.debug("SEv3AdvertisementFormatter=%s" % (rspec,))
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

        values = [{"id": "se-node_%d" % (i)} for i in range(0, offset)]
        return values, last_urn

    def __test_nodes(self, values):
        if len(values) == 0:
            raise geni_ex.GENIv3SearchFailedError(
                "No resources in the given slice-urns")

    @enter_method_log
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        nodes, last_slice_urn = self.__test_urns(urns, 3)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_str_status(n) for n in nodes]
        manifest = self.__manifest()

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {'geni_rspec': "%s" % manifest,
                'geni_urn': last_slice_urn,
                'geni_slivers': slivers}

    def __sliver_str_status(self, dpid):
        return {'geni_sliver_urn': dpid.get("id"),
                'geni_expires': self.__datetime2str(datetime.datetime.now()),
                'geni_allocation_status': self.ALLOCATION_STATE_ALLOCATED,
                'geni_operational_status': self.OPERATIONAL_STATE_READY,
                'geni_error': ""}

    def __sliver_date_status(self, link, etime=None):
        t = datetime.datetime.now() if (etime is None) else etime
        return {'geni_sliver_urn': link.get("id"),
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

    def __manifest(self):
        rspec_ = rspec_manager.get_SERMv3ManifestFormatter()

        node = rspec_manager.get_TNNode("urn:publicid:aist-se1",
                                      "urn:publicid:IDN+AIST+authority+serm")
        if_ = rspec_manager.get_Interface("urn:publicid:aist-se1:if2")
        if_.add_vlan(name="urn:publicid:aist-se1:if2+vlan", tag="25")
        node.add_interface(if_.serialize())
        if_ = rspec_manager.get_Interface("urn:publicid:aist-se1:if3")
        if_.add_vlan(name="urn:publicid:aist-se1:if3+vlan", tag="1983")
        node.add_interface(if_.serialize())

        rspec_.node(node.serialize())

        link = rspec_manager.get_SELink("urn:publicid:aist-se1:if2-if3",
                                        "urn:felix+vlan_trans",
                                        "urn:publicid:IDN+AIST+authority+serm",
                                        vlantag="1980-1989",
                                        sliver="SE-RM reservationID")
        link.add_interface_ref("urn:publicid:aist-se1:if2")
        link.add_interface_ref("urn:publicid:aist-se1:if3")

        rspec_.link(link.serialize())
        return rspec_

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec_ = rspec_manager.get_SERMv3RequestParser(from_string=rspec)
        logger.debug("SEv3RequestParser=%s" % (rspec_,))
        (result, error) = rspec_manager.call_validate(rspec_.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))

        logger.info("Validation success!")
        nodes = rspec_.nodes()
        logger.info("Nodes=%s" % nodes)

        links = rspec_.links()
        logger.info("Links=%s" % links)

        slivers = [self.__sliver_date_status(l) for l in links]
        manifest = self.__manifest()

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        (result, error) = rspec_manager.call_validate(manifest.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))
        else:
            logger.info("RSpec validation success!")
        return ("%s" % manifest, slivers)

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        nodes, last_slice_urn = self.__test_urns(urns, 6)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_date_status(n, expiration_time)
                   for n in nodes]
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
        nodes, last_slice_urn = self.__test_urns(urns, 2)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
        return "test-status-slice_urn-se", slivers

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        nodes, last_slice_urn = self.__test_urns(urns, 3)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        nodes, last_slice_urn = self.__test_urns(urns, 4)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")
