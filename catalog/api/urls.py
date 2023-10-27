from django.urls import path

from catalog.api import views

urlpatterns = [
    path('courses/', views.CatalogCourseListView.as_view(), name='catalog-course-list'),
    path('courses/<uuid:pk>/', views.CatalogCourseView.as_view(), name='catalog-course-view'),
    path('courses/<uuid:pk>/enroll/', views.course_enroll, name='catalog-course-enroll'),
]
