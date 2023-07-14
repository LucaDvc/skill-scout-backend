from django.urls import path
from . import views
from .views import VideoLessonStepListCreateView, VideoLessonStepRetrieveUpdateDestroyView

urlpatterns = [
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<uuid:pk>/', views.CourseRetrieveUpdateDestroyView.as_view(), name='course-retrieve-update-destroy'),

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

    path('lessons/<uuid:lesson_id>/video-steps/', VideoLessonStepListCreateView.as_view(),
         name='video-step-list-create'),
    path('video-steps/<uuid:pk>/', VideoLessonStepRetrieveUpdateDestroyView.as_view(),
         name='video-step-retrieve-update-destroy'),
]
