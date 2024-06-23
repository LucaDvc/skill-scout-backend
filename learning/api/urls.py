from django.urls import path

from learning.api import views

urlpatterns = [
    path('courses/', views.LearnerCourseListView.as_view(), name='learner-course-list'),
    path('courses/<uuid:pk>/', views.LearnerCourseView.as_view(), name='learner-course-get'),
    path('courses/<uuid:pk>/drop/', views.drop_course, name='drop-course'),
    path('courses/favourites/', views.FavouriteCoursesListView.as_view(), name='favourite-courses-list'),

    path('progress/steps/<uuid:step_id>/', views.complete_lesson_step, name='complete-lesson-step'),

    path('code-challenge-steps/<uuid:pk>/submit/', views.CodeChallengeView.as_view(), name='submit-code-challenge'),
    path('code-challenge-steps/<uuid:pk>/', views.CodeChallengeView.as_view(), name='get-code-challenge'),
    path('code-challenge-steps/submissions/<str:task_id>/', views.CodeChallengeResultView.as_view(),
         name='check-code-challenge'),

    path('quiz-steps/<uuid:pk>/', views.QuizStepView.as_view(), name='quiz-read-submit'),
    path('sorting-steps/<uuid:pk>/', views.SortingStepView.as_view(), name='sorting-read-submit'),
    path('text-problems/<uuid:pk>/', views.TextProblemView.as_view(), name='text-problem-read-submit'),

    path('courses/<uuid:course_id>/reviews/', views.ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<uuid:pk>/', views.ReviewRetrieveUpdateDestroyView.as_view(), name='review-retrieve-update-destroy'),
    path('courses/<uuid:course_id>/user-review/', views.get_user_course_review, name='get-user-course-review'),

    path('analytics/engagement/', views.send_engagement_data, name='send-step-engagement'),
]
