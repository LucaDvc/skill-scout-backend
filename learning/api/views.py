from django.shortcuts import get_list_or_404
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from .serializers import LearnerCourseSerializer
from courses.models import Course
from rest_framework.permissions import IsAuthenticated

from ..models import LearnerProgress


class LearnerCourseListView(generics.ListAPIView):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        user = self.request.user
        courses = self.get_queryset()

        learner_progress_list = LearnerProgress.objects.filter(learner__user=user, course__in=courses)

        context.update({
            'learner_progress_list': learner_progress_list
        })
        return context


class LearnerCourseView(generics.RetrieveAPIView):
    serializer_class = LearnerCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        learner = self.request.user

        learner_progress = LearnerProgress.objects.filter(learner=learner, course=self.get_object())

        context.update({
            'learner_progress': learner_progress
        })
        return context
