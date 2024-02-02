# courses/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from courses import cache_utils
from users.models import User
from courses.models import Course, Category, Tag, Chapter, Lesson, BaseLessonStep, TextLessonStep, ProgrammingLanguage
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
