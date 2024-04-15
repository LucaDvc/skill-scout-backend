from django.urls import path

from catalog.api import views

urlpatterns = [
    path('web/courses/', views.WebCatalogCourseListView.as_view(), name='web-catalog-course-list'),
    path('mobile/courses/', views.MobileCatalogCourseListView.as_view(), name='mobile-catalog-course-list'),
    path('courses/<uuid:pk>/', views.CatalogCourseView.as_view(), name='catalog-course-view'),
    path('courses/<uuid:pk>/enroll/', views.course_enroll, name='catalog-course-enroll'),
    path('courses/<uuid:pk>/wishlist/', views.course_wishlist, name='catalog-course-wishlist'),

    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
]
