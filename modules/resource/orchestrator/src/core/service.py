from abc import ABCMeta, abstractmethod
from core import log
import threading
import time

logger = log.getLogger("service")


class Service(threading.Thread):
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def do_action(self):
        """ Implement this method that is called every step."""
        pass
    
    def __init__(self, name, interval):
        super(Service, self).__init__(name=name)
        self.__mutex = threading.Lock()
        self.__stop = threading.Event()
        self.__interval = interval
        self.name = name
        self.daemon = True
    
    def __is_stopped(self):
        with self.__mutex:
            return self.__stop.isSet()
    
    def __close(self):
        with self.__mutex:
            self.__stop.set()
    
    def start(self):
        logger.debug("Start the %s service" % (self.name,))
        super(Service, self).start()
    
    def stop(self):
        timeout = self.__interval + 1
        logger.debug("Stop the %s service" % (self.name,))
        self.__close()
        if self.is_alive():
            logger.debug("Joining %dsecs" % (timeout,))
            self.join(timeout=timeout)
    
    def run(self):
        try:
            while not self.__is_stopped():
                self.do_action()
                time.sleep(self.__interval)
        except Exception as e:
            logger.error("RunTime error: %s" % (str(e),))
