from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from jobs import sdn_resource_detector
from core.service import Service
import core
logger = core.log.getLogger('ro-scheduler')

ro_scheduler = None


class ROSchedulerService(Service):
    def __init__(self, interval=30):
        global ro_scheduler
        ro_scheduler = BackgroundScheduler()
        ro_scheduler.add_jobstore('mongodb', database='felix_ro',
                                  collection='ScheduledJobs')
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

    def __oneshot_jobs(self):
        try:
            run_time = datetime.now() + timedelta(seconds=1)
            ro_scheduler.add_job(sdn_resource_detector, 'date',
                                 id='oneshot_sdn_resource_detector',
                                 run_date=run_time)
        except Exception as e:
            logger.warning("oneshot_jobs failure: %s" % (e,))

    def __cron_jobs(self):
        try:
            ro_scheduler.add_job(sdn_resource_detector, 'cron',
                                 id='cron_sdn_resource_detector',
                                 hour=1, minute=0, second=0)
        except Exception as e:
            logger.warning("cron_jobs failure: %s" % (e,))
