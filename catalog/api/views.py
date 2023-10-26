from rest_framework import generics
from rest_framework.generics import get_object_or_404

from catalog.api.serializers import DetailedCatalogCourseSerializer, SimpleCatalogCourseSerializer
from courses.models import Course


class CatalogCourseListView(generics.ListAPIView):
    serializer_class = SimpleCatalogCourseSerializer
    queryset = Course.objects.filter(active=True)


class CatalogCourseView(generics.RetrieveAPIView):
    serializer_class = DetailedCatalogCourseSerializer

    def get_queryset(self):
        return Course.objects.filter(active=True)

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(self.get_queryset(), id=pk)
