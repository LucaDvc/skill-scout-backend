from django.core.cache import cache

from catalog.api.serializers import DetailedCatalogCourseSerializer
from courses.models import ProgrammingLanguage, Category
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist

from learning.api.serializers import LearnerCourseSerializer


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


def get_categories():
    cache_key = 'all_categories'
    category_qs = cache.get(cache_key)

    if not category_qs:
        category_qs = list(Category.objects.all())
        cache.set(cache_key, category_qs, 3600)  # cache for one hour

    return category_qs


def get_learner_course_data(course):
    cached_serialized_course = cache.get(f"learner_course_{course.id}")
    if cached_serialized_course:
        return cached_serialized_course
    else:
        course_data = LearnerCourseSerializer(course, context={'is_learner': True}).data
        cache.set(f"learner_course_{course.id}", course_data, timeout=5400)
        return course_data


def get_catalog_course_data(course):
    cached_serialized_course = cache.get(f"catalog_course_{course.id}")
    if cached_serialized_course:
        return cached_serialized_course
    else:
        course_data = DetailedCatalogCourseSerializer(course).data
        cache.set(f"catalog_course_{course.id}", course_data, timeout=5400)
        return course_data


def cache_test(key):
    obj = cache.get(key)
    if obj:
        print(str(obj))
        print(str(type(obj)))
    print('tested cache')
