from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command


logger = get_task_logger(__name__)


@shared_task
def refresh_catalog_courses_cache():
    logger.info("Refreshing the catalog courses cache...")
    call_command("cache_catalog_courses")


@shared_task
def refresh_learner_courses_cache():
    logger.info("Refreshing the learner courses cache...")
    call_command("cache_learner_courses")
