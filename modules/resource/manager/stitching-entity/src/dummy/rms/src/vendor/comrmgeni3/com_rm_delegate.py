import amsoil.core.pluginmanager as pm
import amsoil.core.log
import datetime
logger = amsoil.core.log.getLogger("crmgeniv3delegate")

GENIv3DelegateBase = pm.getService("geniv3delegatebase")
geni_ex = pm.getService("geniv3exceptions")
rspec_manager = pm.getService("geni3RSpecsManager")


class CRMGENIv3Delegate(GENIv3DelegateBase):
    URN_PREFIX = "urn:CRM_AM"
    MANIFEST_URL = "http://www.geni.net/resources/rspec/3"
    EMULAB_XMLNS = "http://www.protogeni.net/resources/rspec/ext/emulab/1"

    def __init__(self):
        super(CRMGENIv3Delegate, self).__init__()
        logger.info("CRMGENIv3Delegate successfully initialized!")

    def enter_method_log(f):
        as_ = f.func_code.co_varnames[:f.func_code.co_argcount]

        def wrapper(*args, **kwargs):
            ass_ = ", ".join("%s=%r" % e for e in zip(as_, args) +
                             kwargs.items())
            logger.info("Calling %s with args=%s" % (f.func_name, ass_,))
            return f(*args, **kwargs)
        return wrapper

    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        request.xsd"""
        return {"crm": "http://example.com/CRM"}

    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        manifest.xsd"""
        return {"emulab": self.EMULAB_XMLNS}

    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        ad.xsd"""
        return {"crm": "http://example.com/CRM"}

    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers."""
        return "geni_many"
    

    def __create_node(self, prefix, name, exclusive, available, interfaces):
        authority_cm = "urn:publicid:IDN+ocf:i2cat:vtam+authority+cm"
        component_name = prefix + "+node+" + name
        node = rspec_manager.get_COMNode(component_name, component_name, authority_cm, exclusive, available)
        for interface in interfaces:
            node.add_interface(interface)
        return node

    def __create_link(self, prefix, server_name, link_name):
        component_id_and_name = prefix + "+" + server_name + "+link+" + link_name
        link = rspec_manager.get_COMLink(component_id_and_name, component_id_and_name)
        return link

    @enter_method_log
    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec = rspec_manager.get_CRMv3AdvertisementFormatter()
        prefix = "urn:publicid:IDN+ocf:i2cat:vtam"

        # Node: Rodoreda
        name = "Rodoreda"
        node = self.__create_node(prefix, name, "false", "true", [])
        rspec.node(node.serialize())
        # Link: Rodoreda - Switch 3
        link_source = "eth1"
        link_dest = "00:10:00:00:00:00:00:03"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())
        # Link: Rodoreda - Switch 5
        link_source = "eth2"
        link_dest = "00:10:00:00:00:00:00:05"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())

        # Node: March
        name = "March"
        node = self.__create_node(prefix, name, "false", "true", [])
        rspec.node(node.serialize())
        # Link: March - Switch 4
        link_source = "eth1"
        link_dest = "00:10:00:00:00:00:00:04"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())
        # Link: Match - Switch 5
        link_source = "eth2"
        link_dest = "00:10:00:00:00:00:00:05"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())

        # Node: Verdaguer
        name = "Verdaguer"
        node = self.__create_node(prefix, name, "false", "true", [])
        rspec.node(node.serialize())
        # Link: Rodoreda - Switch 1
        link_source = "eth1"
        link_dest = "00:10:00:00:00:00:00:01"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())
        # Link: Rodoreda - Switch 2
        link_source = "eth2"
        link_dest = "00:10:00:00:00:00:00:02"
        link = self.__create_link(prefix, name, link_source + "-" + link_dest)
        link.add_link(prefix + ":" + name + "+interface+" + link_source,
                            "urn:publicid:IDN+ocf:ofam+datapath+" + link_dest,
                            "1024MB/s")
        link.add_type("L2 Link")
        rspec.link(link.serialize())

        logger.debug("CRMv3AdvertisementFormatter=%s" % (rspec,))
        (result, error) = rspec_manager.call_validate(rspec.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))

        logger.info("ListResources success!")
        return "%s" % rspec

    def __datetime2str(self, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S.%fZ")

    def __test_urns(self, urns, offset):
        values, last_urn = [], ""
        for urn in urns:
            if self.urn_type(urn) == "slice":
                last_urn = urn

        values = [{"id": "sdn-dpid_%d" % (i)} for i in range(0, offset)]
        return values, last_urn

    @enter_method_log
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 4)

        sliver = {"description": "test describe geniv3 method",
                  "ref": "geni site",
                  "email": "r.monno@nextworks.it"}

        slivers = [self.__sliver_str_status(d) for d in datapaths]
        manifest = rspec_manager.get_CRMv3ManifestFormatter()
        manifest = self.lxml_to_string(manifest.generate(slivers))

        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))
        return {"geni_rspec": manifest,
                "geni_urn": last_slice_urn,
                "geni_slivers": slivers}

    def __sliver_str_status(self, node):
        return {"geni_sliver_urn": node.get("id"),
                "geni_expires": self.__datetime2str(datetime.datetime.now()),
                "geni_allocation_status": self.ALLOCATION_STATE_ALLOCATED,
                "geni_operational_status": self.OPERATIONAL_STATE_READY,
                "geni_error": ""}

    def __sliver_date_status(self, node, etime=None):
        t = datetime.datetime.now() if (etime is None) else etime
        return {"geni_sliver_urn": node.get("component_manager_id"),
                "geni_expires": t,
                "geni_allocation_status": self.ALLOCATION_STATE_ALLOCATED,
                "geni_operational_status": self.OPERATIONAL_STATE_READY,
                "geni_error": ""}

    def __sliver_details_status(self, node):
        cid = node.get("component_id")
        return {"geni_sliver_urn": cid,
                "geni_expires": datetime.datetime.now(),
                "geni_allocation_status": self.ALLOCATION_STATE_ALLOCATED,
                "geni_operational_status": self.OPERATIONAL_STATE_READY,
                "geni_error": "",
                "geni_resource_status": "some-details-%s" % cid}

    @enter_method_log
    def allocate(self, slice_urn, client_cert, credentials, rspec,
                 end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec = rspec_manager.get_CRMv3RequestParser(from_string=rspec)
        logger.debug("CRMv3RequestParser=%s" % (rspec,))
        (result, error) = rspec_manager.call_validate(rspec.get_rspec())
        if result is not True:
            logger.error("RSpec validation failure: %s" % (error,))
        logger.info("Validation success!")

        slivers = rspec.get_slivers()
        logger.info("Slivers=%s" % slivers)

        slivers = [self.__sliver_date_status(s) for s in slivers]
        manifest = rspec_manager.get_CRMv3ManifestFormatter()
        manifest = self.lxml_to_string(manifest.generate(slivers))
        logger.info("Manifest=%s, Slivers=%s" % (manifest, slivers))

        # Prepare now the request
        
        return (manifest, slivers)

    @enter_method_log
    def renew(self, urns, client_cert, credentials, expiration_time,
              best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 5)

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

        slivers = [self.__sliver_date_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return "test-status-slice_urn", slivers

    @enter_method_log
    def perform_operational_action(self, urns, client_cert, credentials,
                                   action, best_effort):
        datapaths, last_slice_urn = self.__test_urns(urns, 9)

        slivers = [self.__sliver_details_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        datapaths, last_slice_urn = self.__test_urns(urns, 6)

        slivers = [self.__sliver_date_status(d) for d in datapaths]
        logger.info("Slivers=%s" % (slivers))
        return slivers

    @enter_method_log
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        raise geni_ex.GENIv3GeneralError("Method not implemented yet!")
