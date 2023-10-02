from django.core.management.base import BaseCommand
from django.core.cache import cache
import requests
from courses.models import ProgrammingLanguage
from courses import judge0_service


class Command(BaseCommand):
    help = 'Populate ProgrammingLanguage table from Judge0 API and cache in memcached'

    def handle(self, *args, **kwargs):
        # Check if the data is already cached
        cached_lang = cache.get("programming_languages_list")

        if cached_lang:
            self.stdout.write(self.style.SUCCESS('ProgrammingLanguage data is cached.'))
            return

        # If not cached, fetch data from Judge0 API
        try:
            languages = judge0_service.get_languages()
        except requests.HTTPError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            return

        languages_list = []
        for lang_data in languages:
            lang, created = ProgrammingLanguage.objects.get_or_create(id=lang_data['id'], name=lang_data['name'])
            cache.set(f"programming_language_{lang.id}", lang, timeout=None)
            languages_list.append(lang)

        # cache the languages list indefinitely
        cache.set("programming_languages_list", languages_list, timeout=None)

        self.stdout.write(self.style.SUCCESS('ProgrammingLanguage table populated and cached successfully.'))
