"""
Parses the settings configuration file and returns a dictionary with all the data.

@date: Jul 16, 2013
@author: CarolinaFernandez (i2CAT)
"""

from StringIO import StringIO
import ConfigParser
import log
import os
import sys

logger = log.getLogger("config-parser")


class ConfParser:
    
    def __init__(self, path):
        """
        Constructor. Reads and parses every setting defined in a config file.
        
        @param path relative URI (to MessageSpreader) for the configuration file
        @throws Exception when configuration directive is wrongly processed
        """
        self.settings = {}
        try:
            confparser = ConfigParser.SafeConfigParser()
            # Deployment location
            path = os.path.join(os.path.split(os.path.abspath(__file__))[0], "../../conf", path)
            # Parse data previously to ignore tabs, spaces or others
            conf_data = StringIO('\n'.join(line.strip() for line in open(path)))
            confparser.readfp(conf_data)
            
            for section in confparser.sections():
                self.settings[section] = {}
                for (key,val) in confparser.items(section):
                    if key == "topics":
                        try:
                            val = [ v.strip() for v in val.split(",") ]
                        except:
                            logger.exception("Could not process topics: %s" % str(val))
                            sys.exit("Could not process topics: %s" % str(val))
                    self.settings[section][key] = val
        except Exception, e:
            logger.exception("Could not parse configuration file '%s'. Details: %s" % (str(path), str(e)))
            sys.exit("Could not parse configuration file '%s'. Details: %s" % (str(path), str(e)))
        self.__dict__.update(self.settings)
    
    def get(self, key):
        """
        Access internal dictionary and retrieve value from given key.
        
        @param key dictionary key to access
        @return value for desired key
        """
        return self.__dict__.get(key, None)
