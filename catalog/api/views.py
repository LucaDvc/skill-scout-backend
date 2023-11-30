from django.db.models import Avg
from django_filters import rest_framework as filters

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.api.filters import MultiFieldSearchFilter, CourseFilter
from catalog.api.serializers import DetailedCatalogCourseSerializer, SimpleCatalogCourseSerializer, \
    CategoryListSerializer
from courses.models import Course, Category
from learning.models import CourseEnrollment


class CatalogCourseListView(generics.ListAPIView):
    serializer_class = SimpleCatalogCourseSerializer
    queryset = Course.objects.annotate(avg_rating=Avg('review__rating')).filter(active=True)
    filter_backends = [MultiFieldSearchFilter, filters.DjangoFilterBackend]
    filterset_class = CourseFilter


class CatalogCourseView(generics.RetrieveAPIView):
    serializer_class = DetailedCatalogCourseSerializer

    def get_queryset(self):
        return Course.objects.filter(active=True)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def course_enroll(request, pk):
    user = request.user

    course = get_object_or_404(Course, id=pk)

    if not course.active:
        return Response({'error': 'enrollment is closed for this course'}, status=status.HTTP_400_BAD_REQUEST)

    enrollment, created = CourseEnrollment.objects.get_or_create(course=course, learner=user)
    if not created:
        return Response({'error': 'learner already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({}, status=status.HTTP_201_CREATED)

# TODO: CATALOG HOME PAGE


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(supercategory__isnull=True)  # Top-level categories only
    serializer_class = CategoryListSerializer
