DEFAULT_XMLNS = "http://www.geni.net/resources/rspec/3"
DEFAULT_XS = "http://www.w3.org/2001/XMLSchema-instance"
DEFAULT_OPENFLOW = "http://www.geni.net/resources/rspec/ext/openflow/3"

DSL_PREFIX = "http://www.geni.net/resources/rspec/"
DEFAULT_SCHEMA_LOCATION = DSL_PREFIX + "3 "
DEFAULT_SCHEMA_LOCATION += DSL_PREFIX + "ext/openflow/3 "

CONTROLLER_TYPE_PRIMARY = "primary"
CONTROLLER_TYPE_MONITOR = "monitor"
CONTROLLER_TYPE_BACKUP = "backup"

NODE_OPENFLOW = "openflow-switch"


def validate(ingress_root):
    import urllib2
    from lxml import etree

    xs = ingress_root.nsmap.get("xs")
    schemas = ingress_root.attrib.get("{%s}schemaLocation" % (xs))
    if len(schemas) == 0:
        return (False, "Unable to find schemas locations!")

    errors = []
    for schema in schemas.split():
        try:
            contents = urllib2.urlopen(schema)
            parser = etree.XMLParser(ns_clean=True, recover=True,
                                     remove_blank_text=True,
                                     remove_comments=True)
            doc = etree.parse(contents, parser)
            xmlschema = etree.XMLSchema(doc)
            if xmlschema.validate(ingress_root):
                return (True, "")

        except Exception as e:
            errors.append(str(e))

    return (False, errors)


class Datapath(object):
    def __init__(self, component_id, component_manager_id, dpid):
        self.datapath = {'component_id': component_id,
                         'component_manager_id': component_manager_id,
                         'dpid': dpid,
                         'ports': []}

    def add_port(self, num, name=None):
        self.datapath['ports'].append({'num': str(num), 'name': name})

    def serialize(self):
        return self.datapath


class Match(object):
    def __init__(self):
        self.use_groups = []
        self.datapaths = []
        self.packet = None

    def add_use_group(self, name):
        self.use_groups.append({'name': name})

    def add_datapath(self, dpath):
        self.datapaths.append({'datapath': dpath})

    def set_packet(self, dl_src=None, dl_dst=None, dl_type=None, dl_vlan=None,
                   nw_src=None, nw_dst=None, nw_proto=None,
                   tp_src=None, tp_dst=None):
        self.packet = {'dl_src': dl_src,
                       'dl_dst': dl_dst,
                       'dl_type': dl_type,
                       'dl_vlan': dl_vlan,
                       'nw_src': nw_src,
                       'nw_dst': nw_dst,
                       'nw_proto': nw_proto,
                       'tp_src': tp_src,
                       'tp_dst': tp_dst}

    def __repr__(self):
        return "use_groups: %s, datapaths: %s, packet: %s" %\
               (self.use_groups, self.datapaths, self.packet)


class OFLink(object):
    def __init__(self, component_id):
        self.link = {'component_id': component_id,
                     'dpids': [],
                     'ports': []}

    def add_datapath(self, dpath):
        self.link['dpids'].append(dpath.serialize())

    def add_port(self, pnum):
        self.link['ports'].append({'port_num': str(pnum)})

    def serialize(self):
        return self.link


class FEDLink(object):
    def __init__(self, component_id):
        self.link = {'component_id': component_id,
                     'link_type_name': None,
                     'component_manager_name': None,
                     'interface_ref_id': []}

    def set_link_type(self, name):
        self.link['link_type_name'] = name

    def set_component_manager(self, name):
        self.link['component_manager_name'] = name

    def add_interface_id(self, ifid):
        self.link['interface_ref_id'].append(ifid)

    def serialize(self):
        return self.link
