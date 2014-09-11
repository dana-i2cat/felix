DEFAULT_XMLNS = "http://www.geni.net/resources/rspec/3"
DEFAULT_XS = "http://www.w3.org/2001/XMLSchema-instance"

DSL_PREFIX = "http://www.geni.net/resources/rspec/"
DEFAULT_SCHEMA_LOCATION = DSL_PREFIX + "3 "


def validate(ingress_root):
    import urllib2
    from lxml import etree

    xs = ingress_root.nsmap.get("xs")
    schemas = ingress_root.attrib.get("{%s}schemaLocation" % (xs))
    if (schemas is None) or (len(schemas) == 0):
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


# Data Models
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
