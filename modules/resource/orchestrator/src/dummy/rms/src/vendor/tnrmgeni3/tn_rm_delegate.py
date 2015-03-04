import amsoil.core.pluginmanager as pm
import amsoil.core.log
import datetime
logger = amsoil.core.log.getLogger('tnrmgeniv3delegate')

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')
rspec_manager = pm.getService('geni3RSpecsManager')


class TNRMGENI3Delegate(GENIv3DelegateBase):
    URN_PREFIX = 'urn:TNRM_AM'
    MANIFEST_URL = 'http://www.geni.net/resources/rspec/ext/tn/3'

    def __init__(self):
        super(TNRMGENI3Delegate, self).__init__()
        logger.info("TNRMGENI3Delegate successfully initialized!")

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
        return {'tn': self.MANIFEST_URL}

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

    def __create_tn_link(self, lid, id1, id2, cap1, cap2):
        l = Link(lid, "urn:publicid:IDN+AIST+authority+cm")
        l.add_interface_ref(id1)
        l.add_interface_ref(id2)
        l.add_property(id1, id2, cap1)
        l.add_property(id2, id1, cap2)
        return l

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Use the advRspec file directly!"""
        with open("vendor/tnrmgeni3/adv-rspec.xml") as f:
            rspec = f.read()
            logger.info("AdvRspec=%s" % (rspec,))
            return rspec

    def list_resources_old(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec = rspec_manager.get_TNRMv3AdvertisementFormatter()
        # node = domain
        tn_node = rspec_manager.get_TNNode("urn:publicid:tn-network1",
                                         "urn:publicid:IDN+NSI+authority+tnrm",
                                         "false")
        # if-1
        if_ = rspec_manager.get_Interface("urn:publicid:tn:aist:network1+" +
                                          "urn:ogf:network:aist:network1:stp1")
        if_.add_vlan(name="urn:publicid:tn:aist:network1+" +
                          "urn:ogf:network:aist:network1:stp1+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())
        # if-2
        if_ = rspec_manager.get_Interface("urn:publicid:tn:aist:network1+" +
                                          "urn:ogf:network:aist:network1:stp2")
        if_.add_vlan(name="urn:publicid:tn:aist:network1+" +
                          "urn:ogf:network:aist:network1:stp2+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())
        # if-3
        if_ = rspec_manager.get_Interface(
            "urn:publicid:tn:i2cat:network1+urn:felix:i2cat-stp1")
        if_.add_vlan(name="urn:publicid:tn:i2cat:network1+" +
                          "urn:felix:i2cat-stp1+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())
        # if-4
        if_ = rspec_manager.get_Interface(
            "urn:publicid:tn:i2cat:network1+urn:felix:i2cat-stp2")
        if_.add_vlan(name="urn:publicid:tn:i2cat:network1+" +
                          "urn:felix:i2cat-stp1+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())
        # if-5
        if_ = rspec_manager.get_Interface("urn:ogf:network:xxx:stp1")
        if_.add_vlan(name="urn:ogf:network:xxx:stp1+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())
        # if-6
        if_ = rspec_manager.get_Interface("urn:ogf:network:yyy:stp2")
        if_.add_vlan(name="urn:ogf:network:xxx:stp2+vlan",
                     descr="1980-1989")
        tn_node.add_interface(if_.serialize())

        rspec.node(tn_node.serialize())

        logger.debug("TNRMv3AdvertisementFormatter=%s" % (rspec,))
        (result, error) = rspec_manager.call_validate(rspec.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))
        else:
            logger.info("RSpec validation success!")

        logger.info("list-resources success!")
        return "%s" % rspec
#        # XXX DEBUG
#        return open("vendor/tnrmgeni3/tn_rm_listresources.xml").read()

    def __datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%fZ')

    def __test_urns(self, urns, offset):
        values, last_urn = [], ""
        for urn in urns:
            if self.urn_type(urn) == "slice":
                last_urn = urn

        values = [{"id": "tn-node_%d" % (i)} for i in range(0, offset)]
        return values, last_urn

    def __test_nodes(self, values):
        if len(values) == 0:
            raise geni_ex.GENIv3SearchFailedError(
                "No resources in the given slice-urns")

    @enter_method_log
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        nodes, last_slice_urn = self.__test_urns(urns, 5)
        self.__test_nodes(nodes)

        slivers = [self.__sliver_str_status(n) for n in nodes]
        manifest = self.__manifest()

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {'geni_rspec': "%s" % manifest,
                'geni_urn': last_slice_urn,
                'geni_slivers': slivers}

    def __sliver_str_status(self, node):
        return {'geni_sliver_urn': node.get("id"),
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

    def __manifest_custom(self):
        with open("vendor/tnrmgeni3/manifest-rspec.xml") as f:
            return f.read()

    def __manifest(self):
        rspec_ = rspec_manager.get_TNRMv3ManifestFormatter()

        node = rspec_manager.get_TNNode("urn:publicid:tn-network1:",
                                      "urn:publicid:IDN+NSI+authority+tnrm")
        if_ = rspec_manager.get_Interface("urn:publicid:tn:aist:network1+" +
                                          "urn:ogf:network:aist:network1:stp1")
        if_.add_vlan(name="urn:publicid:tn:aist:network1+" +
                          "urn:ogf:network:aist:network1:stp1+vlan",
                     tag="1983")
        node.add_interface(if_.serialize())
        if_ = rspec_manager.get_Interface("urn:ogf:network:xxx:stp1")
        node.add_interface(if_.serialize())
        if_ = rspec_manager.get_Interface("urn:ogf:network:yyy:stp2")
        node.add_interface(if_.serialize())
        if_ = rspec_manager.get_Interface(
            "urn:publicid:tn-network1+urn:felix:i2cat-stp2")
        if_.add_vlan(name="urn:publicid:tn-network1+urn:felix:i2cat-stp2+vlan",
                     tag="1983")
        node.add_interface(if_.serialize())

        rspec_.node(node.serialize())

        link = rspec_manager.get_TNLink("urn:publicid:tn-network1:link",
                                        "urn:publicid:IDN+AIST+authority+tnrm",
                                        vlantag="1980-1989")
        link.add_interface_ref("urn:publicid:tn:aist:network1+" +
                               "urn:ogf:network:aist:network1:stp1")
        link.add_interface_ref("urn:ogf:network:xxx:stp1")
        link.add_interface_ref("urn:ogf:network:yyy:stp2")
        link.add_interface_ref("urn:publicid:tn-network1+urn:felix:i2cat-stp2")
        link.add_property("urn:publicid:tn:aist:network1+" +
                          "urn:ogf:network:aist:network1:stp1",
                          "urn:publicid:tn-network1+urn:felix:i2cat-stp2",
                          "1000")
        link.add_property("urn:publicid:tn-network1+urn:felix:i2cat-stp2",
                          "urn:publicid:tn-network1+urn:felix:i2cat-stp2",
                          "500")

        rspec_.link(link.serialize())
        return rspec_

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec_ = rspec_manager.get_TNRMv3RequestParser(from_string=rspec)
        logger.debug("TNRMv3RequestParser=%s" % (rspec_,))
        (result, error) = rspec_manager.call_validate(rspec_.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))

        logger.info("Validation success!")
        nodes = rspec_.nodes()
        logger.info("Nodes=%s" % nodes)

        links = rspec_.links()
        logger.info("Links=%s" % links)

        slivers = [self.__sliver_date_status(l) for l in links]
        manifest = self.__manifest_custom()

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        #(result, error) = rspec_manager.call_validate(manifest)
        #if result is not True:
        #    logger.error("RSpec validation failure: %s" % (error,))
        #else:
        #    logger.info("RSpec validation success!")
        return ("%s" % manifest, slivers)

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        nodes, last_slice_urn = self.__test_urns(urns, 2)
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
	nodes, last_slice_urn = self.__test_urns(urns, 9)
	self.__test_nodes(nodes)

	slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
	return "test-status-slice_urn-tn", slivers

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
	nodes, last_slice_urn = self.__test_urns(urns, 4)
	self.__test_nodes(nodes)

	slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
	return slivers

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
	nodes, last_slice_urn = self.__test_urns(urns, 1)
	self.__test_nodes(nodes)

	slivers = [self.__sliver_date_status(n) for n in nodes]
        logger.info("Slivers=%s" % (slivers))
	return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")
