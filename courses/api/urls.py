from django.urls import path

from courses.api import views

urlpatterns = [
    path('programming-languages/', views.ProgrammingLanguageListView.as_view(), name='programming-languages-list'),
]
