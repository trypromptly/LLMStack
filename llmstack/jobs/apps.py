import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.models.functions import Now

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    name = "llmstack.jobs"
    label = "jobs"

    def ready(self):
        if settings.ENABLE_JOBS is False:
            logger.info("Jobs are disabled")
            return

        try:
            self.reschedule_cron_jobs()
            self.reschedule_repeatable_jobs()
            self.reschedule_scheduled_jobs()
        except BaseException:
            # Django isn't ready yet, example a management command is being
            # executed
            pass

    def reschedule_cron_jobs(self):
        from .models import CronJob

        jobs = CronJob.objects.filter(enabled=True)
        self.reschedule_jobs(jobs)

    def reschedule_repeatable_jobs(self):
        from .models import RepeatableJob

        jobs = RepeatableJob.objects.filter(enabled=True)
        self.reschedule_jobs(jobs)

    def reschedule_scheduled_jobs(self):
        from .models import ScheduledJob

        jobs = ScheduledJob.objects.filter(
            enabled=True,
            scheduled_time__lte=Now(),
        )
        self.reschedule_jobs(jobs)

    def reschedule_jobs(self, jobs):
        for job in jobs:
            if job.is_scheduled() is False:
                logger.info("Scheduling job: {}".format(job))
                # job.save()
