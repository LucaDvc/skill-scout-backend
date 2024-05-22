from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Course
from teaching.models import CourseCompletionAnalytics


@receiver(post_save, sender=Course)
def create_course_completion_analytics(sender, instance, created, **kwargs):
    if created:
        CourseCompletionAnalytics.objects.create(course=instance)
