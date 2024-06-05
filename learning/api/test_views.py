from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from datetime import timedelta

from courses.models import Course, Chapter, Lesson, BaseLessonStep
from learning.models import CourseEnrollment
from teaching.models import EngagementAnalytics
from users.models import User


class EngagementAnalyticsTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create a user
        self.user = User.objects.create_user(
            email='learner@example.com',
            password='testpassword',
            first_name='Learner',
            last_name='Test'
        )
        self.client.force_authenticate(user=self.user)

        # Create another user to be the instructor
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )

        # Create a course
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Test Course'
        )

        CourseEnrollment.objects.create(course=self.course, learner=self.user, active=True, completed=False)

        # Create a chapter
        self.chapter = Chapter.objects.create(
            course=self.course,
            title='Test Chapter'
        )

        # Create a lesson
        self.lesson = Lesson.objects.create(
            chapter=self.chapter,
            title='Test Lesson',
            order=1
        )

        # Create a BaseLessonStep
        self.base_lesson_step = BaseLessonStep.objects.create(
            lesson=self.lesson,
            order=1
        )

        self.engagement_url = reverse('send-step-engagement')

    def test_send_engagement_data(self):
        data = {
            'step_id': self.base_lesson_step.id,
            'time_spent': 120  # 2 minutes in seconds
        }
        response = self.client.post(self.engagement_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Engagement data sent')

        # Verify that the engagement data was recorded correctly
        engagement = EngagementAnalytics.objects.get(learner=self.user, lesson_step=self.base_lesson_step)
        self.assertEqual(engagement.time_spent, timedelta(seconds=120))

    def test_send_engagement_data_without_step_id(self):
        data = {
            'time_spent': 120  # 2 minutes in seconds
        }
        response = self.client.post(self.engagement_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'step_id is required')

    def test_send_engagement_data_forbidden(self):
        # Authenticate as a different user who is not enrolled
        new_user = User.objects.create_user(
            email='new_learner@example.com',
            password='testpassword',
            first_name='NewLearner',
            last_name='Test'
        )
        self.client.force_authenticate(user=new_user)

        data = {
            'step_id': self.base_lesson_step.id,
            'time_spent': 120  # 2 minutes in seconds
        }
        response = self.client.post(self.engagement_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Forbidden')
