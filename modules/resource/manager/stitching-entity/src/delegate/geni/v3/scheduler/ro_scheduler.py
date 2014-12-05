from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from jobs import com_resource_detector, sdn_resource_detector,\
    se_resource_detector, tn_resource_detector, phy_monitoring
from core.service import Service
import core
logger = core.log.getLogger("ro-scheduler")

ro_scheduler = None


class ROSchedulerService(Service):
    def __init__(self, interval=30):
        global ro_scheduler
        ro_scheduler = BackgroundScheduler()
        ro_scheduler.add_jobstore("mongodb", database="felix_ro",
                                  collection="ScheduledJobs")
        ro_scheduler.start()

        # NOTE Interval should be retrieved using the ConfParser from
        # the "resource_detector"."interval" value in the "ro.conf" file
        # Also, consider to considerably increase the interval
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
            ro_scheduler.add_job(func_, "date", id=id_, run_date=run_time)

        except Exception as e:
            logger.warning("oneshot_jobs failure: %s" % (e,))

    def __oneshot_jobs(self):
        self.__add_oneshot(1, com_resource_detector, "oneshot_com_rd")
        self.__add_oneshot(11, sdn_resource_detector, "oneshot_sdn_rd")
        self.__add_oneshot(21, se_resource_detector, "oneshot_se_rd")
        self.__add_oneshot(31, tn_resource_detector, "oneshot_tn_rd")
        self.__add_oneshot(41, phy_monitoring, "oneshot_phy_monitoring")

    def __add_cron(self, func_, id_, hour_, min_, sec_):
        try:
            ro_scheduler.add_job(func_, "cron", id=id_,
                                 hour=hour_, minute=min_, second=sec_)
        except Exception as e:
            logger.warning("cron_jobs failure: %s" % (e,))

    def __cron_jobs(self):
        self.__add_cron(com_resource_detector, "cron_com_rd", 0, 1, 0)
        self.__add_cron(sdn_resource_detector, "cron_sdn_rd", 0, 11, 0)
        self.__add_cron(se_resource_detector, "cron_se_rd", 0, 21, 0)
        self.__add_cron(tn_resource_detector, "cron_tn_rd", 0, 31, 0)
        self.__add_cron(phy_monitoring, "cron_phy_monitoring", 0, 41, 0)
