from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from courses.models import Course, Chapter, Lesson, BaseLessonStep
from .models import CourseCompletionAnalytics
from .tasks import update_learner_progress_for_deleted_item


@receiver(post_save, sender=Course)
def create_course_completion_analytics(sender, instance, created, **kwargs):
    if created:
        CourseCompletionAnalytics.objects.create(course=instance)


@receiver(post_delete, sender=Chapter)
def handle_chapter_delete(sender, instance, **kwargs):
    update_learner_progress_for_deleted_item.delay('chapter', instance.id)


@receiver(post_delete, sender=Lesson)
def handle_lesson_delete(sender, instance, **kwargs):
    update_learner_progress_for_deleted_item.delay('lesson', instance.id)


@receiver(post_delete, sender=BaseLessonStep)
def handle_step_delete(sender, instance, **kwargs):
    update_learner_progress_for_deleted_item.delay('step', instance.id)
