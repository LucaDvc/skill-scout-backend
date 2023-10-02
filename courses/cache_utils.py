from django.core.cache import cache

from courses.models import ProgrammingLanguage
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist


def reset_languages_cache():
    db_languages = list(ProgrammingLanguage.objects.all())
    if not db_languages:
        raise EmptyResultSet('The ProgrammingLanguage table is empty! Run populate_programming_languages command.')

    for lang in db_languages:
        cache.set(f'programming_language_{lang.id}', lang, timeout=None)

    cache.set('programming_languages_list', db_languages, timeout=None)


def get_languages():
    """
    Return a list of ProgrammingLanguage objects from cache or db and a boolean indicating the cache hit.
    """
    cached_languages = cache.get('programming_languages_list')

    if not cached_languages:
        reset_languages_cache()
        return cache.get('programming_languages_list'), False

    return cached_languages, True


def get_language_by_id(lang_id):
    """
    Return a ProgrammingLanguage object from cache or db and a boolean indicating the cache hit.
    """
    cache_key = f'programming_language_{lang_id}'
    cached_language = cache.get(cache_key)

    if cached_language:
        return cached_language, True

    languages, from_cache = get_languages()

    if from_cache:
        language = next((lang for lang in languages if lang.id == lang_id), None)
    else:
        language = cache.get(cache_key)

    if not language:
        raise ObjectDoesNotExist(f'ProgrammingLanguage object with id {lang_id} not found!')

    return language, from_cache


def cache_test(key):
    obj = cache.get(key)
    print(str(obj))
    print(str(type(obj)))
    print('tested cache')
