from django.core.management.base import BaseCommand
from django.core.cache import cache

from courses.models import Course
from learning.api.serializers import LearnerCourseSerializer


class Command(BaseCommand):
    help = 'Cache serialized active courses data for learners'

    def handle(self, *args, **kwargs):
        courses = Course.objects.filter(active=True)

        for course in courses:
            serialized_course = LearnerCourseSerializer(course, context={'is_learner': True}).data
            cache.set(f"learner_course_{course.id}", serialized_course, timeout=5400)
            self.stdout.write(self.style.SUCCESS(f"Course {course.id} cached"))

        self.stdout.write(self.style.SUCCESS('All active learning courses cached'))
