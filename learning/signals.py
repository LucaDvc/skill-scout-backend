from django.db.models.signals import post_save
from django.dispatch import receiver

from learning.models import CourseEnrollment, LearnerProgress


@receiver(post_save, sender=CourseEnrollment)
def create_learner_progress(sender, instance, created, **kwargs):
    if created:
        LearnerProgress.objects.create(course=instance.course, learner=instance.learner)
