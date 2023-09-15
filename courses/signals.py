from django.db.models.signals import post_delete
from django.dispatch import receiver

from courses.models import TextLessonStep, QuizLessonStep, VideoLessonStep


@receiver(post_delete, sender=TextLessonStep)
def delete_text_step_base(sender, instance, **kwargs):
    instance.base_step.delete()


@receiver(post_delete, sender=QuizLessonStep)
def delete_text_step_base(sender, instance, **kwargs):
    instance.base_step.delete()


@receiver(post_delete, sender=VideoLessonStep)
def delete_text_step_base(sender, instance, **kwargs):
    instance.base_step.delete()
