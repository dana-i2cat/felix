#!/usr/bin/python
import sys
import os
import time
import ConfigParser
import tempfile
import codecs
from StringIO import StringIO
from vt_manager.communication.sfa.util.xml import XML
default_config = \
"""
"""

def isbool(v):
    return v.lower() in ("true", "false")

def str2bool(v):
    return v.lower() in ("true", "1")             

class Config:
  
#    def __init__(self, config_file='/etc/sfa/sfa_config'):
#    def __init__(self, config_file='/opt/ofelia/vt_manager/src/python/vt_manager/communication/sfa/configs/config'):
    def __init__(self, config_file=None):
        if not config_file:
            config_file = os.path.join(os.path.dirname(__file__), "../sfa_config/config.py")
        self._files = []
        self.config_path = os.path.dirname(config_file)
        self.config = ConfigParser.ConfigParser()  
        self.filename = config_file
        if not os.path.isfile(self.filename):
            self.create(self.filename)
        self.load(self.filename)
        

    def _header(self):
        header = """
DO NOT EDIT. This file was automatically generated at
%s from:

%s
""" % (time.asctime(), os.linesep.join(self._files))

        # Get rid of the surrounding newlines
        return header.strip().split(os.linesep)

    def create(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        configfile = open(filename, 'w')
        configfile.write(default_config)
        configfile.close()
        

    def load(self, filename):
        if filename:
            try:
                self.config.read(filename)
            except ConfigParser.MissingSectionHeaderError:
                if filename.endswith('.xml'):
                    self.load_xml(filename)
                else:
                    self.load_shell(filename)
            self._files.append(filename)
            self.set_attributes()

    def load_xml(self, filename):
        xml = XML(filename)
        categories = xml.xpath('//configuration/variables/category')
        for category in categories:
            section_name = category.get('id')
            if not self.config.has_section(section_name):
                self.config.add_section(section_name)
            options = category.xpath('./variablelist/variable')
            for option in options:
                option_name = option.get('id')
                value = option.xpath('./value')[0].text
                if not value:
                    value = ""
                self.config.set(section_name, option_name, value)
         
    def load_shell(self, filename):
        f = open(filename, 'r')
        for line in f:
            try:
                if line.startswith('#'):
                    continue
                parts = line.strip().split("=")
                if len(parts) < 2:
                    continue
                option = parts[0]
                value = parts[1].replace('"', '').replace("'","")
                section, var = self.locate_varname(option, strict=False)
                if section and var:
                    self.set(section, var, value)
            except:
                pass
        f.close()               

    def locate_varname(self, varname, strict=True):
        varname = varname.lower()
        sections = self.config.sections()
        section_name = ""
        var_name = ""
        for section in sections:
            if varname.startswith(section.lower()) and len(section) > len(section_name):
                section_name = section.lower()
                var_name = varname.replace(section_name, "")[1:]
        if strict and not self.config.has_option(section_name, var_name):
            raise ConfigParser.NoOptionError(var_name, section_name)
        return (section_name, var_name)             

    def set_attributes(self):
        sections = self.config.sections()
        for section in sections:
            for item in self.config.items(section):
                name = "%s_%s" % (section, item[0])
                value = item[1]
                if isbool(value):
                    value = str2bool(value)
                elif value.isdigit():
                    value = int(value)    
                setattr(self, name, value)
                setattr(self, name.upper(), value)

    def variables(self):
        """
        Return all variables.

        Returns:

        variables = { 'category_id': (category, variablelist) }

        category = { 'id': "category_identifier",
                     'name': "Category name",
                     'description': "Category description" }

        variablelist = { 'variable_id': variable }

        variable = { 'id': "variable_identifier",
                     'type': "variable_type",
                     'value': "variable_value",
                     'name': "Variable name",
                     'description': "Variable description" }
        """

        variables = {}
        for section in self.config.sections():
            category = {
                'id': section,
                'name': section,
                'description': section,
            }
            variable_list = {}
            for item in self.config.items(section):
                var_name = item[0] 
                name = "%s_%s" % (section, var_name)
                value = item[1]
                if isbool(value):
                    value_type = bool
                elif value.isdigit():
                    value_type = int
                else:
                    value_type = str
                variable = {
                    'id': var_name,
                    'type': value_type,
                    'value': value,
                    'name': name,
                    'description': name,
                }
                variable_list[name] = variable
            variables[section] = (category, variable_list)
        return variables      

    def verify(self, config1, config2, validate_method):
        return True

    def validate_type(self, var_type, value):
        return True

    @staticmethod
    def is_xml(config_file):
        try:
            x = Xml(config_file)
            return True     
        except:
            return False

    @staticmethod
    def is_ini(config_file):
        try:
            c = ConfigParser.ConfigParser()
            c.read(config_file)
            return True
        except ConfigParser.MissingSectionHeaderError:
            return False


    def dump(self, sections = []):
        sys.stdout.write(output_python())

    def output_python(self, encoding = "utf-8"):
        buf = codecs.lookup(encoding)[3](StringIO())
        buf.writelines(["# " + line + os.linesep for line in self._header()]) 
        
        for section in self.sections():
            buf.write("[%s]%s" % (section, os.linesep))
            for (name,value) in self.items(section):
                buf.write("%s=%s%s" % (name,value,os.linesep))
            buf.write(os.linesep)
        return buf.getvalue()
                
    def output_shell(self, show_comments = True, encoding = "utf-8"):
        """
        Return variables as a shell script.
        """

        buf = codecs.lookup(encoding)[3](StringIO())
        buf.writelines(["# " + line + os.linesep for line in self._header()])

        for section in self.sections():
            for (name,value) in self.items(section):
                # bash does not have the concept of NULL
                if value:
                    option = "%s_%s" % (section.upper(), name.upper())
                    if isbool(value):
                        value = str(str2bool(value))
                    elif not value.isdigit():
                        value = '"%s"' % value  
                    buf.write(option + "=" + value + os.linesep)
        return buf.getvalue()        

    def output_php(selfi, encoding = "utf-8"):
        """
        Return variables as a PHP script.
        """

        buf = codecs.lookup(encoding)[3](StringIO())
        buf.write("<?php" + os.linesep)
        buf.writelines(["// " + line + os.linesep for line in self._header()])

        for section in self.sections():
            for (name,value) in self.items(section):
                option = "%s_%s" % (section, name)
                buf.write(os.linesep)
                buf.write("// " + option + os.linesep)
                if value is None:
                    value = 'NULL'
                buf.write("define('%s', %s);" % (option, value) + os.linesep)

        buf.write("?>" + os.linesep)

        return buf.getvalue()    

    def output_xml(self, encoding = "utf-8"):
        pass

    def output_variables(self, encoding="utf-8"):
        """
        Return list of all variable names.
        """

        buf = codecs.lookup(encoding)[3](StringIO())
        for section in self.sections():
            for (name,value) in self.items(section):
                option = "%s_%s" % (section,name) 
                buf.write(option + os.linesep)

        return buf.getvalue()
        pass 
        
    def write(self, filename=None):
        if not filename:
            filename = self.filename
        configfile = open(filename, 'w') 
        self.config.write(configfile)
    
    def save(self, filename=None):
        self.write(filename)


    def get_trustedroots_dir(self):
        return self.config_path + os.sep + 'trusted_roots'

    def get_openflow_aggrMgr_info(self):
        aggr_mgr_ip = 'localhost'
        if (hasattr(self,'openflow_aggregate_manager_ip')):
            aggr_mgr_ip = self.OPENFLOW_AGGREGATE_MANAGER_IP

        aggr_mgr_port = 2603
        if (hasattr(self,'openflow_aggregate_manager_port')):
            aggr_mgr_port = self.OPENFLOW_AGGREGATE_MANAGER_PORT

        return (aggr_mgr_ip,aggr_mgr_port)

    def get_interface_hrn(self):
        if (hasattr(self,'sfa_interface_hrn')):
            return self.SFA_INTERFACE_HRN
        else:
            return "plc"

    def __getattr__(self, attr):
	print self.config.__dict__.keys()
        return getattr(self.config, attr)

if __name__ == '__main__':
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        config = Config(filename)
    else:    
        config = Config()
    config.dump()
    
