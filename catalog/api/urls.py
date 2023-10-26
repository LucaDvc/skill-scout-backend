from django.urls import path

from catalog.api import views

urlpatterns = [
    path('', views.CatalogCourseListView.as_view(), name='catalog-course-list'),
    path('course/<uuid:pk>', views.CatalogCourseView.as_view(), name='catalog-course-view'),
]
