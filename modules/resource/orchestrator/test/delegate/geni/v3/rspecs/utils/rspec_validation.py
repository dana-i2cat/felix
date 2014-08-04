from lxml import etree
import urllib2
    
def validate(ingress_root):
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
