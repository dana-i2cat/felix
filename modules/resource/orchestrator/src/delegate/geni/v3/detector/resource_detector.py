import threading
import time

from abc import ABCMeta, abstractmethod

from core import log
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

    def __isStopped(self):
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
            while not self.__isStopped():
                self.do_action()
                time.sleep(self.__interval)

        except Exception as e:
            logger.error("RunTime error: %s" % (str(e),))


class ResourceDetector(Service):
    """This object can be used to populate the internal RO db
       with the available resources exposed by RMs."""
    def __init__(self, interval=30):
        super(ResourceDetector, self).__init__("ResourceDetector", interval)

    def info(self, msg):
        logger.info("[%s] %s" % (self.name, msg,))

    def do_action(self):
        self.info("Do proper action here!")
