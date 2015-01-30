from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from core.service import Service
import core
logger = core.log.getLogger("se-scheduler")

se_scheduler = None


class SESchedulerService(Service):
    def __init__(self,interval=2):
        global se_scheduler
        se_scheduler = BackgroundScheduler()
        se_scheduler.add_jobstore("mongodb", database="felix_se",
                                  collection="ScheduledJobs")
        print "!!!!!!!"
        se_scheduler.start()
        super(SESchedulerService, self).__init__("SESchedulerService",interval)
        self.first_time = True
        print "!!!!!!!2"
    @staticmethod
    def get_scheduler():
        return se_scheduler

    def do_action(self):
        jobs = se_scheduler.get_jobs()
        logger.debug("Scheduled Jobs=%s" % (jobs,))


    def stop(self):
        se_scheduler.shutdown()
        logger.info("se_scheduler shutdown")
        super(SESchedulerService, self).stop()

    def __add_oneshot(self, secs_, func_, id_):
        try:
            run_time = datetime.now() + timedelta(seconds=secs_)
            se_scheduler.add_job(func_, "date", id=id_, run_date=run_time)

        except Exception as e:
            logger.warning("oneshot_jobs failure: %s" % (e,))



