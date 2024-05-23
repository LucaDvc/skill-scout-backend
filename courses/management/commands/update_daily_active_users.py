from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from courses.models import Course
from teaching.models import EngagementAnalytics, DailyActiveUsersAnalytics


class Command(BaseCommand):
    help = 'Update daily active user analytics for all courses'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # Loop through all courses and update active users
        for course in Course.objects.all():
            active_users_count = EngagementAnalytics.objects.filter(
                lesson_step__lesson__chapter__course=course,
                last_accessed__date=today
            ).values('learner').distinct().count()

            # Update or create the record for the current day
            daily_analytics, created = DailyActiveUsersAnalytics.objects.get_or_create(
                course=course,
                date=today,
                defaults={'active_users': active_users_count}
            )

            if not created:
                daily_analytics.active_users = active_users_count
                daily_analytics.save()

        self.stdout.write(self.style.SUCCESS('Updated daily active users for all courses'))
