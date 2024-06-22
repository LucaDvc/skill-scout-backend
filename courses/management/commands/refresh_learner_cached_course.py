from uuid import UUID

from django.core.management.base import BaseCommand
from django.core.cache import cache
from courses.models import Course
from learning.api.serializers import LearnerCourseSerializer


class Command(BaseCommand):
    help = 'Refresh learner cache for a specific course'

    def add_arguments(self, parser):
        parser.add_argument('course_id', type=UUID, help='The ID of the course to refresh cache for')

    def handle(self, *args, **kwargs):
        course_id = kwargs['course_id']
        try:
            course = Course.objects.get(id=course_id)
            serialized_course = LearnerCourseSerializer(course, context={'is_learner': True}).data
            cache.set(f"learner_course_{course.id}", serialized_course, timeout=5400)
            self.stdout.write(self.style.SUCCESS(f"Course {course_id} cache refreshed"))
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Course {course_id} does not exist"))
