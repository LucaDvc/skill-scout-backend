from django.urls import path

from learning.api import views

urlpatterns = [
    path('courses/', views.LearnerCourseListView.as_view(), name='learner-course-list'),
    path('courses/<uuid:pk>/', views.LearnerCourseView.as_view(), name='learner-course-get'),

    path('code-challenge-steps/<uuid:pk>/submit/', views.submit_code_challenge, name='submit-code-challenge'),
    path('code-challenge-steps/submissions/<str:task_id>/', views.check_code_challenge_result, name='check-code-challenge'),

    path('progress/steps/<uuid:step_id>/', views.complete_lesson_step, name='complete-lesson-step'),

    path('quiz-steps/<uuid:pk>/submit/', views.submit_quiz, name='submit-quiz'),
    path('quiz-steps/<uuid:pk>/', views.get_quiz_step, name='get-quiz-step'),

    path('courses/<uuid:course_id>/reviews/', views.ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<uuid:pk>/', views.ReviewRetrieveUpdateDestroyView.as_view(), name='review-retrieve-update-destroy'),
    path('courses/<uuid:course_id>/user-review/', views.get_user_course_review, name='get-user-course-review'),

    path('courses/favourites/', views.FavouriteCoursesListView.as_view(), name='favourite-courses-list'),

    path('analytics/engagement/', views.send_engagement_data, name='send-step-engagement'),
]
