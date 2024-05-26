from django.db.models import Avg, Count, Value, F
from django.db.models.functions import Coalesce
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
    CategoryListSerializer, MobileCatalogCourseSerializer
from courses import cache_utils
from courses.api.serializers import TagSerializer, CourseReviewsSerializer
from courses.models import Course, Category, Tag, Review
from learning.models import CourseEnrollment


class BaseCatalogCourseListView(generics.ListAPIView):
    ordering_fields = ['avg_rating', 'title', 'price', 'enrolled_learners', 'reviews_no']
    filter_backends = [MultiFieldSearchFilter, filters.DjangoFilterBackend, OrderingFilter]
    pagination_class = type('StandardPagination', (PageNumberPagination,), {'page_size': 20})
    filterset_class = CourseFilter

    def get_queryset(self):
        return (Course.objects.filter(active=True)
                .annotate(avg_rating=Coalesce(Avg('review__rating'), Value(0.0)))
                .annotate(enrolled_learners_count=Count('enrolled_learners', distinct=True))
                .annotate(reviews_no=Count('review')))

    def filter_queryset(self, queryset):
        ordering = self.request.query_params.get("ordering", "")
        if ordering.lstrip('-') == 'enrolled_learners':
            ordering = '-enrolled_learners_count' if ordering.startswith('-') else 'enrolled_learners_count'
        ordering_fields = ['avg_rating', 'title', 'price', 'enrolled_learners_count', 'reviews_no']
        # Check if ordering is requested on a valid field
        if ordering.lstrip('-') in ordering_fields:
            # Determine if we are ordering in ascending or descending order
            if ordering.startswith('-'):
                field_name = ordering.lstrip('-')
                # For fields that may have null values, specify nulls_last=True for descending order
                queryset = queryset.order_by(F(field_name).desc(nulls_last=True))
            else:
                field_name = ordering
                # For fields that may have null values, specify nulls_first=True for ascending order
                queryset = queryset.order_by(F(field_name).asc(nulls_first=True))
        else:
            # Apply default filtering and ordering
            queryset = super().filter_queryset(queryset)

        return queryset


class WebCatalogCourseListView(BaseCatalogCourseListView):
    serializer_class = SimpleCatalogCourseSerializer


class MobileCatalogCourseListView(BaseCatalogCourseListView):
    serializer_class = MobileCatalogCourseSerializer
    pagination_class = type('MobilePagination', (PageNumberPagination,), {'page_size': 10})


class CatalogCourseView(generics.RetrieveAPIView):
    serializer_class = DetailedCatalogCourseSerializer

    def get_queryset(self):
        return Course.objects.filter(active=True)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)

    def retrieve(self, request, *args, **kwargs):
        course = self.get_object()
        course_data = cache_utils.get_catalog_course_data(course)

        return Response(course_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def course_enroll(request, pk):
    user = request.user

    course = get_object_or_404(Course, id=pk)

    if not course.active:
        return Response({'error': 'enrollment is closed for this course'}, status=status.HTTP_400_BAD_REQUEST)

    enrollment, created = CourseEnrollment.objects.get_or_create(course=course, learner=user)

    if course in user.wishlist.all():
        user.wishlist.remove(course)

    if not created:
        return Response({'error': 'learner already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def course_wishlist(request, pk):
    """
        Add or remove a course from the user's wishlist
    """
    user = request.user

    course = get_object_or_404(Course, id=pk)

    if not course.active:
        return Response({'error': 'course is inactive'}, status=status.HTTP_400_BAD_REQUEST)

    if course in user.wishlist.all():
        user.wishlist.remove(course)
        return Response({}, status=status.HTTP_200_OK)
    else:
        user.wishlist.add(course)
        return Response({}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    user = request.user
    courses = user.wishlist.all().annotate(
        avg_rating=Coalesce(Avg('review__rating'), Value(0.0)),
        enrolled_learners_count=Count('enrolled_learners', distinct=True)
    )
    serializer = SimpleCatalogCourseSerializer(courses, many=True)

    return Response(serializer.data)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(supercategory__isnull=True)  # Top-level categories only
    serializer_class = CategoryListSerializer


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CourseReviewsListView(generics.ListAPIView):
    serializer_class = CourseReviewsSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['creation_date', 'rating']

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, id=course_id)
        return Review.objects.filter(course=course)

    def calculate_percentage(self, count, total):
        return round((count / total * 100), 1) if total > 0 else 0

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        ordered_queryset = self.filter_queryset(queryset)

        total_reviews = ordered_queryset.count()
        avg_rating = ordered_queryset.aggregate(Avg('rating'))['rating__avg'] or 0
        avg_rating = round(avg_rating, 1)

        rating_counts = ordered_queryset.values('rating').annotate(count=Count('rating')).order_by('rating')

        counts = {i: 0 for i in range(1, 6)}
        for rc in rating_counts:
            counts[int(rc['rating'])] = rc['count']

        percentage_five_star = self.calculate_percentage(counts[5], total_reviews)
        percentage_four_star = self.calculate_percentage(counts[4], total_reviews)
        percentage_three_star = self.calculate_percentage(counts[3], total_reviews)
        percentage_two_star = self.calculate_percentage(counts[2], total_reviews)
        percentage_one_star = self.calculate_percentage(counts[1], total_reviews)

        serializer = self.get_serializer({
            'reviews': ordered_queryset,
            'avg_rating': avg_rating,
            'percentage_five_star': percentage_five_star,
            'percentage_four_star': percentage_four_star,
            'percentage_three_star': percentage_three_star,
            'percentage_two_star': percentage_two_star,
            'percentage_one_star': percentage_one_star
        })
        return Response(serializer.data)
