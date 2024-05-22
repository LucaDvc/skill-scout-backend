from django.test import TestCase
from courses.models import Course
from teaching.models import CourseCompletionAnalytics
from users.models import User


class CourseSignalTest(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )

    def test_create_course_completion_analytics(self):
        # Create a new course with the instructor
        new_course = Course.objects.create(title='New Test Course', instructor=self.instructor)

        # Check if a CourseCompletionAnalytics instance was created for the new course
        self.assertTrue(CourseCompletionAnalytics.objects.filter(course=new_course).exists())
