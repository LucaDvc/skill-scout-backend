from django.db.models import Q
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters, NumberFilter
from django_filters import CharFilter

from courses import cache_utils
from courses.models import Course


class MultiFieldSearchFilter(SearchFilter):
    """
    Custom search filter that searches in multiple fields.
    """
    def get_search_query(self, request):
        search_query = request.query_params.get(self.search_param, None)
        return search_query.split() if search_query else None

    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_query(request)

        if not search_terms:
            return queryset

        # construct the search query using OR for all terms and fields
        query = Q()
        for term in search_terms:
            query |= Q(title__icontains=term)
            query |= Q(description__icontains=term)
            query |= Q(intro__icontains=term)
            query |= Q(category__name__icontains=term)
            query |= Q(tags__name__icontains=term)
            query |= Q(instructor__first_name__icontains=term)
            query |= Q(instructor__last_name__icontains=term)

        return queryset.filter(query)


class CourseFilter(filters.FilterSet):
    average_rating__gte = NumberFilter(method='filter_average_rating_gte')
    average_rating__lte = NumberFilter(method='filter_average_rating_lte')
    category = CharFilter(method='filter_by_category_name')

    class Meta:
        model = Course
        fields = {
            'price': ['lte', 'gte'],
        }

    def filter_average_rating_gte(self, queryset, name, value):
        return queryset.filter(avg_rating__gte=value)

    def filter_average_rating_lte(self, queryset, name, value):
        return queryset.filter(avg_rating__lte=value)

    def filter_by_category_name(self, queryset, name, value):
        """
        This filter first finds the category by name, then gets all courses
        in that category or its subcategories.
        """
        category_qs = cache_utils.get_categories()

        supercategory = next((category for category in category_qs if category.name == value), None)
        if not supercategory:
            return queryset

        subcategories = [category for category in category_qs if category.supercategory_id == supercategory.id]

        # construct the OR conditions for the queryset
        q_objects = Q(category=supercategory)
        for subcategory in subcategories:
            q_objects |= Q(category=subcategory)

        return queryset.filter(q_objects)

