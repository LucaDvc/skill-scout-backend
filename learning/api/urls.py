from django.urls import path

from learning.api import views

urlpatterns = [
    path('courses/', views.LearnerCourseListView.as_view(), name='learner-course-list'),
    path('courses/<uuid:pk>/', views.LearnerCourseView.as_view(), name='learner-course-get')
]
