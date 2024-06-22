from celery import shared_task
from django.db import transaction
from learning.models import LearnerProgress

BATCH_SIZE = 1000  # Adjust the batch size according to your needs


@shared_task
def update_learner_progress_for_deleted_item(item_type, item_id):
    if item_type == 'chapter':
        with transaction.atomic():
            learner_progresses = LearnerProgress.objects.filter(completed_chapters__contains=[item_id])
            update_in_batches(learner_progresses, 'completed_chapters', item_id)

    elif item_type == 'lesson':
        with transaction.atomic():
            learner_progresses = LearnerProgress.objects.filter(completed_lessons__contains=[item_id])
            update_in_batches(learner_progresses, 'completed_lessons', item_id)

    elif item_type == 'step':
        with transaction.atomic():
            learner_progresses = LearnerProgress.objects.filter(completed_steps__contains=[item_id])
            update_in_batches(learner_progresses, 'completed_steps', item_id)


def update_in_batches(queryset, field_name, item_id):
    while queryset.exists():
        batch = list(queryset[:BATCH_SIZE])
        for progress in batch:
            # Remove the item from the list
            updated_list = array_remove(getattr(progress, field_name), item_id)
            setattr(progress, field_name, updated_list)

        LearnerProgress.objects.bulk_update(batch, [field_name])


def array_remove(array, element):
    return [x for x in array if x != element]
