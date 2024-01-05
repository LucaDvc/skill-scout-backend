from django.db.models import Avg, Count
from django_filters import rest_framework as filters

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from catalog.api.filters import MultiFieldSearchFilter, CourseFilter
from catalog.api.serializers import DetailedCatalogCourseSerializer, SimpleCatalogCourseSerializer, \
    CategoryListSerializer
from courses.api.serializers import TagSerializer
from courses.models import Course, Category, Tag
from learning.models import CourseEnrollment


class CatalogCourseListView(generics.ListAPIView):
    serializer_class = SimpleCatalogCourseSerializer
    ordering_fields = ['avg_rating,', 'title', 'price', 'enrolled_learners', 'reviews_no']
    filter_backends = [MultiFieldSearchFilter, filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = CourseFilter
    pagination_class = type('StandardPagination', (PageNumberPagination,), {'page_size': 20})

    def get_queryset(self):
        return (Course.objects.filter(active=True)
                .annotate(avg_rating=Avg('review__rating'))
                .annotate(enrolled_learners_count=Count('enrolled_learners'))
                .annotate(reviews_no=Count('review')))

    def filter_queryset(self, queryset):
        ordering = self.request.query_params.get("ordering", "")

        if ordering in ['avg_rating', '-avg_rating']:
            queryset = super().filter_queryset(queryset.order_by(ordering))
        elif ordering in ['enrolled_learners', '-enrolled_learners']:
            queryset = super().filter_queryset(queryset.order_by(f'{ordering}_count'))
        elif ordering in ['reviews_no', '-reviews_no']:
            queryset = super().filter_queryset(queryset.order_by(ordering))
        else:
            # Apply default filtering and ordering
            queryset = super().filter_queryset(queryset)

        return queryset


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


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(supercategory__isnull=True)  # Top-level categories only
    serializer_class = CategoryListSerializer


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
