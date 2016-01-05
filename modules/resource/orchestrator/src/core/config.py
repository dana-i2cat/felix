"""
Parses the settings configuration file and returns a
dictionary with all the data.

@date: Jul 16, 2013
@author: CarolinaFernandez (i2CAT)
"""

from StringIO import StringIO
import ConfigParser
import json
import log
import os
import sys

logger = log.getLogger("config-parser")


class BaseParser:

    def __init__(self, path):
        """
        Constructor. Reads and parses every setting defined in a config file.

        @param path name of the configuration file
        @throws Exception when configuration directive is wrongly processed
        """
        self.settings = {}
        self.path = os.path.join(os.path.split(
            os.path.abspath(__file__))[0], "../../conf", path)

    def get(self, key):
        """
        Access internal dictionary and retrieve value from given key.

        @param key dictionary key to access
        @return value for desired key
        """
        return self.__dict__.get(key, None)


class ConfParser(BaseParser):

    def __init__(self, path):
        """
        Constructor. Reads and parses every setting defined in a config file.

        @param path name of the configuration file
        @throws Exception when configuration directive is wrongly processed
        """
        BaseParser.__init__(self, path)
        try:
            confparser = ConfigParser.SafeConfigParser()
            # Parse data previously to ignore tabs, spaces or others
            conf_data = StringIO("\n".join(l.strip() for l in open(self.path)))
            parse_ok = True
            try:
                confparser.readfp(conf_data)
            # Error reading: eg. bad value substitution (bad format in strings)
            except ConfigParser.InterpolationMissingOptionError, e:
                confparser.read(conf_data)
                parse_ok = False
            # Do some post-processing of the conf sections
            self.__process_conf_sections(confparser, parse_ok)
        except Exception, e:
            exception_desc = "Could not parse configuration file '%s'. Details:\
                %s" % (str(self.path), str(e))
            logger.exception(exception_desc)
            sys.exit(exception_desc)
        self.__dict__.update(self.settings)

    def __process_conf_sections(self, confparser, parse_ok):
        """
        Parses every setting defined in a config file.

        @param confparser SafeConfigParser object
        @throws Exception when configuration directive is wrongly processed
        """
        for section in confparser.sections():
            self.settings[section] = {}
            try:
                confparser_items = confparser.items(section)
            except:
                confparser_items = confparser._sections.items()
                parse_ok = False
            for (key, val) in confparser_items:
                if parse_ok:
                    if key == "topics":
                        try:
                            val = [v.strip() for v in val.split(",")]
                        except:
                            exception_desc = "Could not process topics: \
                                %s" % str(val)
                            logger.exception(exception_desc)
                            sys.exit(exception_desc)
                    self.settings[section][key] = val
                else:
                    try:
                        for v in val.items():
                            if v[0] != "__name__":
                                self.settings[section][v[0]] = \
                                    str(v[1]).replace('\"', '')
                    except Exception as e:
                        exception_desc = "Cannot process item: %s. \
                            Details: %s" % str(val, e)
                        logger.exception(exception_desc)
                        sys.exit(exception_desc)


class JSONParser(BaseParser):

    def __init__(self, path):
        """
        Constructor. Reads the JSON config file.

        @param path name of the configuration file
        @throws Exception when configuration directive is wrongly processed
        """
        BaseParser.__init__(self, path)
        try:
            with open(self.path) as data_file:
                self.settings = json.load(data_file)
        except Exception, e:
            exception_desc = "Could not parse JSON configuration file '%s'. \
                Details: %s" % (str(self.path), str(e))
            logger.exception(exception_desc)
            sys.exit(exception_desc)
        self.__dict__.update(self.settings)


class FullConfParser(BaseParser):

    def __init__(self):
        BaseParser.__init__(self, "")
        self.__load_files()

    def __load_files(self):
        for f in os.listdir(self.path):
            if f.endswith(".conf"):
                self.__dict__.update({str(f): ConfParser(f).settings})
            elif f.endswith(".json"):
                self.__dict__.update({str(f): JSONParser(f).settings})
