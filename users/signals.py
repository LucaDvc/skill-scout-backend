from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User, Instructor, Learner


@receiver(post_save, sender=User)
def create_related_profiles(sender, instance, created, **kwargs):
    if created:
        Instructor.objects.create(user=instance)
        Learner.objects.create(user=instance)
