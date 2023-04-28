from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<uuid:pk>/', views.CourseRetrieveUpdateDestroyView.as_view(), name='course-retrieve-update-destroy'),
    path('courses/<uuid:course_id>/chapters/', views.ChapterListCreateView.as_view(), name='chapter-list-create'),
    path('chapters/<uuid:pk>/', views.ChapterRetrieveUpdateDestroyView.as_view(), name='chapter-retrieve-update-destroy'),
    path('chapters/<uuid:chapter_id>/lessons/', views.LessonListCreateView.as_view(), name='lesson-list-create'),
    path('lessons/<uuid:pk>/', views.LessonRetrieveUpdateDestroyView.as_view(), name='lesson-retrieve-update-destroy')
]
