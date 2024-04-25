from django.core.management.base import BaseCommand
from django.core.cache import cache

from catalog.api.serializers import DetailedCatalogCourseSerializer
from courses.models import Course


class Command(BaseCommand):
    help = 'Cache serialized active courses data for catalog detailed view'

    def handle(self, *args, **kwargs):
        courses = Course.objects.filter(active=True)

        for course in courses:
            serialized_course = DetailedCatalogCourseSerializer(course).data
            cache.set(f"catalog_course_{course.id}", serialized_course, timeout=5400)
            self.stdout.write(self.style.SUCCESS(f"Course {course.id} cached"))

        self.stdout.write(self.style.SUCCESS('All active courses cached'))
