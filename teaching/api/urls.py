from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<uuid:pk>/', views.CourseRetrieveUpdateDestroyView.as_view(), name='course-retrieve-update-destroy'),

    path('courses/<uuid:course_id>/enrolled_learners/', views.CourseEnrolledLearnersListView.as_view(),
         name='course-enrolled-learners'),

    path('courses/<uuid:course_id>/chapters/', views.ChapterListCreateView.as_view(), name='chapter-list-create'),
    path('chapters/<uuid:pk>/', views.ChapterRetrieveUpdateDestroyView.as_view(),
         name='chapter-retrieve-update-destroy'),

    path('chapters/<uuid:chapter_id>/lessons/', views.LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<uuid:pk>/', views.LessonRetrieveUpdateDestroyView.as_view(), name='lesson-retrieve-update-destroy'),

    path('lessons/<uuid:lesson_id>/text-steps/', views.TextLessonStepListCreateView.as_view(),
         name='text-step-list-create'),
    path('text-steps/<uuid:pk>/', views.TextLessonStepRetrieveUpdateDestroyView.as_view(),
         name='text-step-retrieve-update-destroy'),

    path('lessons/<uuid:lesson_id>/quiz-steps/', views.QuizLessonStepListCreateView.as_view(),
         name='quiz-step-list-create'),
    path('quiz-steps/<uuid:pk>/', views.QuizLessonStepRetrieveUpdateDestroyView.as_view(),
         name='quiz-step-retrieve-update-destroy'),

    path('quiz-steps/<uuid:quiz_id>/quiz-choices/', views.QuizChoiceListCreateView.as_view(),
         name='quiz-choice-list-create'),
    path('quiz-choices/<uuid:pk>/', views.QuizChoiceRetrieveUpdateDestroyView.as_view(),
         name='quiz-choice-retrieve-update-destroy'),

    path('lessons/<uuid:lesson_id>/video-steps/', views.VideoLessonStepListCreateView.as_view(),
         name='video-step-list-create'),
    path('video-steps/<uuid:pk>/', views.VideoLessonStepRetrieveUpdateDestroyView.as_view(),
         name='video-step-retrieve-update-destroy'),

    path('lessons/<uuid:lesson_id>/code-challenge-steps/', views.CodeChallengeLessonStepListCreateView.as_view(),
         name='code-challenge-step-list-create'),
    path('code-challenge-steps/<uuid:pk>/', views.CodeChallengeLessonStepRetrieveUpdateDestroyView.as_view(),
         name='code-challenge-step-retrieve-update-destroy'),

    path('code-challenge-steps/<uuid:code_challenge_id>/test_cases/',
         views.CodeChallengeTestCaseListCreateView.as_view(),
         name='test-case-list-create'),
    path('test_cases/<int:pk>/', views.CodeChallengeTestCaseRetrieveUpdateDestroyView.as_view(),
         name='test-case-retrieve-update-destroy'),

    path('analytics/<uuid:course_id>/enrollment/', views.get_enrollment_analytics, name='enrollment-analytics'),
    path('analytics/<uuid:course_id>/completion/', views.get_course_completion_analytics, name='completion-analytics'),
    path('analytics/<uuid:course_id>/activity/', views.get_daily_activity_analytics, name='activity-analytics'),
    path('analytics/<uuid:course_id>/steps-engagement/', views.get_lesson_steps_engagement_analytics,
         name='steps-engagement-analytics'),
    path('analytics/<uuid:course_id>/lessons-engagement/', views.get_lessons_engagement_analytics,
         name='lessons-engagement-analytics'),
    path('analytics/<uuid:course_id>/assessments/', views.get_course_assessments_analytics,
         name='assessments-analytics'),
]
