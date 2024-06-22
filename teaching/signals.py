from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from courses.models import Course, Chapter, Lesson, BaseLessonStep, QuizLessonStep, CodeChallengeLessonStep, \
    SortingProblemLessonStep, TextProblemLessonStep
from .models import CourseCompletionAnalytics
from .tasks import update_learner_progress_for_deleted_item, refresh_learner_course_cache


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


@receiver(post_save, sender=QuizLessonStep)
@receiver(post_save, sender=CodeChallengeLessonStep)
@receiver(post_save, sender=SortingProblemLessonStep)
@receiver(post_save, sender=TextProblemLessonStep)
def invalidate_course_cache(sender, instance, **kwargs):
    course_id = instance.base_step.lesson.chapter.course.id
    cache.delete(f"learner_course_{course_id}")
    refresh_learner_course_cache.delay(course_id)
