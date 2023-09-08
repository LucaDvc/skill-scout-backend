from rest_framework import generics
from rest_framework.generics import get_object_or_404

from courses.api.serializers import CourseSerializer
from courses.models import Course
from rest_framework.permissions import IsAuthenticated


class LearnerCourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)


class LearnerCourseView(generics.RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(enrolled_learners__user=user)

    def get_object(self):
        course_id = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=course_id)
