DEFAULT_XMLNS = "http://www.geni.net/resources/rspec/3"
DEFAULT_XS = "http://www.w3.org/2001/XMLSchema-instance"

DSL_PREFIX = "http://www.geni.net/resources/rspec/"
DEFAULT_SCHEMA_LOCATION = DSL_PREFIX + "3 "

PROTOGENI_PREFIX = "http://www.protogeni.net/resources/rspec/0.1"


def validate(ingress_root):
    import urllib2
    from lxml import etree

    # Both can work
    xs_xsi = ingress_root.nsmap.get("xs") or ingress_root.nsmap.get("xsi")
    schemas = ingress_root.attrib.get("{%s}schemaLocation" % xs_xsi)
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
            try:
                xmlschema.assertValid(ingress_root)
                return (True, "")

            except Exception as e:
                errors.append(str(e))

        except Exception as e:
            errors.append(str(e))

    return (False, errors)


def validate_namespaces(rspec_string):
    """
    Intended to validate against multiple schemas
    """
    import urllib2
    from lxml import etree

    rspec_root = etree.fromstring(rspec_string)
    sl = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
    schema_locations = rspec_root.get(sl)
    validate = True
    if schema_locations:
        schema_location_list = filter(
            lambda x: ".xsd" in x, schema_locations.split(" "))
        # try to download the schema
        xmlschema_contents = urllib2.urlopen(schema_location_list[0])
        xmlschema_doc = etree.parse(xmlschema_contents)
        errors = []
        for n, sl in enumerate(schema_location_list[1:], start=1):
            try:
                imp = '{http://www.w3.org/2001/XMLSchema}import'
                xmlschema_doc_new_import = etree.Element(
                    imp, schemaLocation="%s" % sl)
                xmlschema_doc.getroot().insert(0, xmlschema_doc_new_import)
            except Exception as e:
                errors.append(str(e))
        xmlschema = etree.XMLSchema(xmlschema_doc)
        # validate RSpec against specified schemaLocations
        validate &= xmlschema.validate(rspec_root)
    if validate:
        errors = ""
    return (validate, errors)


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
