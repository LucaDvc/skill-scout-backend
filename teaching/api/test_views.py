# courses/tests.py
from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from learning.models import LearnerQuizPerformance, CodeChallengeSubmission
from teaching.models import DailyActiveUsersAnalytics, EngagementAnalytics
from users.models import User
from courses.models import Course, Category, Tag, Chapter, Lesson, BaseLessonStep, TextLessonStep, ProgrammingLanguage, \
    QuizLessonStep, CodeChallengeLessonStep
from django.core.cache import cache


class CourseListCreateViewTest(APITestCase):
    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user('testuser@test.com', 'password', 'Test', 'User')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create categories and tags if needed
        self.category = Category.objects.create(name='Development')
        self.tag1 = Tag.objects.create(name='Python')
        self.tag2 = Tag.objects.create(name='Django')

        # URL for creating and listing courses
        self.url = reverse('course-list-create')

        # Create a course
        self.course = Course.objects.create(instructor=self.user, title='Course 1', category=self.category)
        self.chapter = Chapter.objects.create(course=self.course, title='Chapter 1')
        self.lesson = Lesson.objects.create(chapter=self.chapter, title='Lesson 1', order=1)
        base_step = BaseLessonStep.objects.create(lesson=self.lesson, order=1)
        self.lesson_step = TextLessonStep.objects.create(text='Some text', base_step=base_step)
        self.programming_language = ProgrammingLanguage.objects.create(id=71, name='Python')

    def tearDown(self):
        # Clear the cache after each test
        cache.clear()

    def test_list_courses_with_nested_structure(self):
        # Make a GET request to the list endpoint
        response = self.client.get(self.url)

        # Check that the response is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The response data should include the nested structure
        # Check that the response contains one course
        self.assertEqual(len(response.data), 1)

        # Check that the course contains chapters
        self.assertEqual(len(response.data[0]['chapters']), 1)

        # Check that the chapter contains lessons
        self.assertEqual(len(response.data[0]['chapters'][0]['lessons']), 1)

        # Check that the lesson contains lesson steps
        self.assertEqual(len(response.data[0]['chapters'][0]['lessons'][0]['lesson_steps']), 1)

        # Check that the lesson step is a text step
        self.assertEqual(response.data[0]['chapters'][0]['lessons'][0]['lesson_steps'][0]['type'], 'text')

        # Check that the lesson step contains the text
        self.assertEqual(response.data[0]['chapters'][0]['lessons'][0]['lesson_steps'][0]['text'], 'Some text')

    def test_list_courses(self):
        # Create a few courses
        course_1 = Course.objects.create(instructor=self.user, title='Course 1', category=self.category)
        course_2 = Course.objects.create(instructor=self.user, title='Course 2', category=self.category)

        # Make a GET request to the list endpoint
        response = self.client.get(self.url)

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response contains 3 courses (one from setUp).
        self.assertEqual(len(response.data), 3)

        course_1.delete()
        course_2.delete()

    def test_create_nested_course(self):
        category = Category.objects.get(name='Development')
        # Data to create a new course
        data = {
            "title": "Django Mastery Course",
            "category": category.id,
            "intro": "This is an intro to the course",
            "description": "Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Aenean eu leo quam.",
            "requirements": "Python basics",
            "total_hours": "30",
            "chapters": [
                {
                    "title": "Getting Started",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Intro",
                            "chapter_id": "3def5c73-e3dc-4435-8c53-57e459c00ae5",
                            "lesson_steps": []
                        },
                        {
                            "order": 2,
                            "title": "What is Django?",
                            "chapter_id": "3def5c73-e3dc-4435-8c53-57e459c00ae5",
                            "lesson_steps": [
                                {
                                    "order": 1,
                                    "type": "codechallenge",
                                    "title": "First code challenge12",
                                    "description": "very cool problem",
                                    "language_id": 71,
                                    "initial_code": None,
                                    "proposed_solution": None,
                                    "test_cases": [
                                        {
                                            "input": "MTA=",
                                            "expected_output": "MjA="
                                        },
                                        {
                                            "input": "MjA=",
                                            "expected_output": "MzA="
                                        },
                                        {
                                            "input": "MzA=",
                                            "expected_output": "NDA="
                                        },
                                        {
                                            "input": "NDA=",
                                            "expected_output": "NTA="
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "title": "Templates & Static Files",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Module Introduction",
                            "lesson_steps": []
                        },
                        {
                            "order": 2,
                            "title": "Adding & Registering Templates",
                            "lesson_steps": [
                                {
                                    "type": "text",
                                    "order": 1,
                                    "text": "some random text 3"
                                }
                            ]
                        }
                    ]
                }
            ],
            "price": "0",
            "image": "https://courses-platform-bucket.s3.eu-north-1.amazonaws.com/courses/images/skill_scout_logo_white_background.png",
            "tags": [
                {
                    "id": "f7e58360-ae85-4417-be1e-69e9aab00b7e",
                    "name": "Web Development"
                },
                {
                    "id": "f0dcaec7-8469-4bdf-bdd3-6f675a4ecbfd",
                    "name": "Python"
                }
            ],
            "active": False,
            "level": "1"
        }

        # Make a POST request to the create endpoint
        response = self.client.post(self.url, data, format='json')

        # Check that the response is 201 CREATED.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that a Course instance has been created.
        self.assertEqual(Course.objects.count(), 2)
        # Check that the course's instructor is the logged-in user.
        self.assertEqual(Course.objects.first().instructor, self.user)


class GetCourseCompletionAnalyticsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )
        self.course = Course.objects.create(title='Test Course', instructor=self.user)
        self.url = reverse('completion-analytics', kwargs={'course_id': self.course.id})
        self.client.force_authenticate(user=self.user)

    def test_get_course_completion_analytics(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('learners_completed', response.data)
        self.assertIn('learners_in_progress', response.data)


class GetEnrollmentAnalyticsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )
        self.course = Course.objects.create(title='Test Course', instructor=self.user)
        self.url = reverse('enrollment-analytics', kwargs={'course_id': self.course.id})
        self.client.force_authenticate(user=self.user)

    def test_get_enrollment_analytics(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)


class GetActivityAnalyticsTest(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )

        # Create a course with a release date
        self.course = Course.objects.create(
            title='Test Course', instructor=self.user, release_date=date.today() - timedelta(days=60)
        )

        # Create some DailyActiveUsersAnalytics data for the last 5 days
        self.analytics_data = [
            DailyActiveUsersAnalytics.objects.create(
                course=self.course, date=date.today() - timedelta(days=i), active_users=i*10
            )
            for i in range(5)
        ]

        # Set the URL
        self.url = reverse('activity-analytics', kwargs={'course_id': self.course.id})

    def test_get_activity_analytics_default_date_range(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Since default date range includes last 30 days, all 5 records should be included
        self.assertEqual(len(response.data), 5)
        # Check the values of active_users
        for i, entry in enumerate(response.data):
            self.assertEqual(entry['active_users'], (4 - i) * 10)

    def test_get_activity_analytics_custom_date_range(self):
        self.client.force_authenticate(user=self.user)
        start_date = (date.today() - timedelta(days=4)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'startDate': start_date, 'endDate': end_date})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Since we're fetching the last 5 days of data, all 5 records should be included
        self.assertEqual(len(response.data), 5)
        # Check the values of active_users
        for i, entry in enumerate(response.data):
            self.assertEqual(entry['active_users'], (4 - i) * 10)

    def test_get_activity_analytics_partial_date_range(self):
        self.client.force_authenticate(user=self.user)
        start_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'startDate': start_date})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Since we're fetching from 2 days ago to today, 3 records should be included
        self.assertEqual(len(response.data), 3)
        # Check the values of active_users
        for i, entry in enumerate(response.data):
            self.assertEqual(entry['active_users'], (2 - i) * 10)

    def test_get_activity_analytics_no_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetCourseEngagementAnalyticsTest(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )

        # Create a course, chapter & lessons
        self.course = Course.objects.create(
            title='Test Course', instructor=self.user, release_date=timezone.now() - timedelta(days=60)
        )
        self.chapter = Chapter.objects.create(course=self.course, title='Chapter 1')
        self.lessons = [
            Lesson.objects.create(chapter=self.chapter, title=f'Lesson {i+1}', order=i+1)
            for i in range(3)
        ]

        # Create BaseLessonStep and EngagementAnalytics data
        self.lesson_steps = []
        for lesson in self.lessons:
            for i in range(3):  # Each lesson has 3 steps
                step = BaseLessonStep.objects.create(lesson=lesson, order=i+1)
                self.lesson_steps.append(step)
                EngagementAnalytics.objects.create(
                    learner=self.user,
                    course=self.course,
                    lesson_step=step,
                    time_spent=timedelta(minutes=30 * (i + 1)),
                    last_accessed=timezone.now() - timedelta(days=i)
                )

    def test_get_lesson_steps_engagement_analytics(self):
        url = reverse('steps-engagement-analytics', kwargs={'course_id': self.course.id})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

        # Check the values of lesson steps and other fields
        for i, entry in enumerate(response.data):
            lesson_step = self.lesson_steps[i]
            self.assertEqual(entry['lesson_step_id'], str(lesson_step.id))
            self.assertEqual(entry['lesson_step_order'], lesson_step.order)
            self.assertEqual(entry['lesson_title'], lesson_step.lesson.title)
            self.assertEqual(entry['average_time_spent'].total_seconds(), 1800 * (i % 3 + 1))
            self.assertEqual(entry['learners_count'], 1)
            self.assertIn('lesson_step_type', entry)
            self.assertIn('last_accessed', entry)

    def test_get_lessons_engagement_analytics(self):
        url = reverse('lessons-engagement-analytics', kwargs={'course_id': self.course.id})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Check the values of average_time_spent and other fields
        for i, entry in enumerate(response.data):
            lesson = self.lessons[i]
            lesson_steps = [step for step in self.lesson_steps if step.lesson == lesson]
            avg_time_spent = sum((step.engagementanalytics_set.first().time_spent.total_seconds() for step in lesson_steps)) / len(lesson_steps)
            self.assertEqual(entry['lesson_id'], str(lesson.id))
            self.assertEqual(entry['lesson_order'], lesson.order)
            self.assertEqual(entry['lesson_title'], lesson.title)
            self.assertAlmostEqual(entry['average_time_spent'].total_seconds(), avg_time_spent, delta=1)
            self.assertEqual(entry['learners_count'], 1)  # All steps have the same single learner
            self.assertIn('last_accessed', entry)


class CourseAssessmentAnalyticsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a user
        self.user = User.objects.create_user(
            email='instructor@example.com',
            password='testpassword',
            first_name='Instructor',
            last_name='Test'
        )
        self.client.force_authenticate(user=self.user)

        # Create a course
        self.course = Course.objects.create(
            instructor=self.user,
            title='Test Course'
        )

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

        # Create a BaseLessonSteps
        self.quiz_base_lesson_step = BaseLessonStep.objects.create(
            lesson=self.lesson,
            order=1
        )
        self.code_base_lesson_step = BaseLessonStep.objects.create(
            lesson=self.lesson,
            order=2
        )

        # Create a QuizLessonStep
        self.quiz_lesson_step = QuizLessonStep.objects.create(
            base_step=self.quiz_base_lesson_step,
            question='Test Question',
            explanation='Test Explanation'
        )

        # Create a CodeChallengeLessonStep
        self.language = ProgrammingLanguage.objects.create(
            id=1,
            name='Python'
        )
        self.code_challenge_lesson_step = CodeChallengeLessonStep.objects.create(
            base_step=self.code_base_lesson_step,
            title='Test Code Challenge',
            description='Test Description',
            initial_code='print("Hello, World!")',
            language=self.language,
            proposed_solution='print("Hello, World!")'
        )

        # Create LearnerQuizPerformance
        self.learner_quiz_performance = LearnerQuizPerformance.objects.create(
            learner=self.user,
            quiz_step=self.quiz_lesson_step,
            attempts=1,
            passed=True
        )

        # Create CodeChallengeSubmission
        self.code_challenge_submission = CodeChallengeSubmission.objects.create(
            learner=self.user,
            code_challenge_step=self.code_challenge_lesson_step,
            submitted_code='print("Hello, World!")',
            passed=True
        )

    def test_get_course_assessments_analytics(self):
        url = reverse('assessments-analytics', kwargs={'course_id': self.course.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('quiz_statistics', response.data)
        self.assertIn('code_challenge_statistics', response.data)

        # Check quiz statistics
        quiz_stats = response.data['quiz_statistics']
        self.assertEqual(len(quiz_stats), 1)
        self.assertEqual(quiz_stats[0]['chapter'], self.chapter.title)
        self.assertEqual(quiz_stats[0]['lesson'], self.lesson.title)
        self.assertEqual(quiz_stats[0]['step_order'], self.quiz_base_lesson_step.order)
        self.assertEqual(quiz_stats[0]['step_id'], self.quiz_base_lesson_step.id)
        self.assertEqual(quiz_stats[0]['total_attempts'], 1)
        self.assertEqual(quiz_stats[0]['total_learners'], 1)
        self.assertEqual(quiz_stats[0]['success_rate'], 100.0)

        # Check code challenge statistics
        code_challenge_stats = response.data['code_challenge_statistics']
        self.assertEqual(len(code_challenge_stats), 1)
        self.assertEqual(code_challenge_stats[0]['chapter'], self.chapter.title)
        self.assertEqual(code_challenge_stats[0]['lesson'], self.lesson.title)
        self.assertEqual(code_challenge_stats[0]['step_order'], self.code_base_lesson_step.order)
        self.assertEqual(code_challenge_stats[0]['step_id'], self.code_base_lesson_step.id)
        self.assertEqual(code_challenge_stats[0]['total_attempts'], 1)
        self.assertEqual(code_challenge_stats[0]['total_learners'], 1)
        self.assertEqual(code_challenge_stats[0]['success_rate'], 100.0)
