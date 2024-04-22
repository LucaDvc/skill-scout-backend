from rest_framework import generics

from courses import cache_utils
from courses.api.serializers import ProgrammingLanguageSerializer


class ProgrammingLanguageListView(generics.ListAPIView):
    serializer_class = ProgrammingLanguageSerializer

    def get_queryset(self):
        languages, _ = cache_utils.get_languages()
        return languages
