from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from core.config import ConfParser
from core.service import Service
from datetime import datetime, timedelta
from jobs import com_resource_detector, sdn_resource_detector,\
    se_resource_detector, tn_resource_detector, physical_monitoring,\
    slice_monitoring, ro_resource_detector

import ast
import core
logger = core.log.getLogger("ro-scheduler")

ro_scheduler = None


class ROSchedulerService(Service):

    def __init__(self):
        """
        Constructor of the service.
        """
        self.config = ConfParser("ro.conf")
        self.scheduler = self.config.get("scheduler")
        interval = int(self.scheduler.get("frequency"))
        master_ro = self.config.get("master_ro")
        mro_enabled = ast.literal_eval(master_ro.get("mro_enabled"))
        db_name = "felix_ro"
        if mro_enabled:
            db_name = "felix_mro"
        global ro_scheduler
        ro_scheduler = BackgroundScheduler()
        ro_scheduler.add_jobstore(
            MongoDBJobStore(database=db_name, collection="scheduler.jobs"))
        ro_scheduler.start()

        super(ROSchedulerService, self).__init__(
            "ROSchedulerService", interval)
        self.first_time = True

    @staticmethod
    def get_scheduler():
        return ro_scheduler

    def do_action(self):
        jobs = ro_scheduler.get_jobs()
        logger.debug("Scheduled Jobs=%s" % (jobs,))

        if self.first_time:
            self.__oneshot_jobs()
            self.__cron_jobs()
            self.first_time = False

    def stop(self):
        ro_scheduler.shutdown()
        logger.info("ro_scheduler shutdown")
        super(ROSchedulerService, self).stop()

    def __add_oneshot(self, secs_, func_, id_):
        try:
            run_time = datetime.now() + timedelta(seconds=secs_)
            ro_scheduler.add_job(
                func_, trigger=DateTrigger(run_date=run_time), id=id_)

        except Exception as e:
            logger.warning("oneshot_jobs failure: %s" % (e,))

    def __oneshot_jobs(self):
        self.__add_oneshot(int(self.scheduler.get("oneshot_ro")),
                           ro_resource_detector, "oneshot_ro_rd")
        self.__add_oneshot(int(self.scheduler.get("oneshot_com")),
                           com_resource_detector, "oneshot_com_rd")
        self.__add_oneshot(int(self.scheduler.get("oneshot_sdn")),
                           sdn_resource_detector, "oneshot_sdn_rd")
        self.__add_oneshot(int(self.scheduler.get("oneshot_se")),
                           se_resource_detector, "oneshot_se_rd")
        self.__add_oneshot(int(self.scheduler.get("oneshot_tn")),
                           tn_resource_detector, "oneshot_tn_rd")
        self.__add_oneshot(int(self.scheduler.get("oneshot_phy-monit")),
                           physical_monitoring, "oneshot_physical_monitoring")
        self.__add_oneshot(int(self.scheduler.get("oneshot_slice-monit")),
                           slice_monitoring, "oneshot_slice_monitoring")

    def __add_cron(self, func_, id_, hour_, min_, sec_):
        try:
            tr_ = CronTrigger(hour=hour_, minute=min_, second=sec_)
            ro_scheduler.add_job(func_, trigger=tr_, id=id_)
        except Exception as e:
            logger.warning("cron_jobs failure: %s" % (e,))

    def __cron_jobs(self):
        self.__add_cron(ro_resource_detector, "cron_ro_rd", 0, 1, 0)
        self.__add_cron(com_resource_detector, "cron_com_rd", 0, 11, 0)
        self.__add_cron(sdn_resource_detector, "cron_sdn_rd", 0, 21, 0)
        self.__add_cron(se_resource_detector, "cron_se_rd", 0, 31, 0)
        self.__add_cron(tn_resource_detector, "cron_tn_rd", 0, 41, 0)
        self.__add_cron(physical_monitoring, "cron_physical_monitoring",
                        0, 51, 0)
        self.__add_cron(slice_monitoring, "cron_slice_monitoring",
                        1, 1, 0)
