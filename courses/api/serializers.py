import logging
from uuid import UUID

from django.db import transaction
from rest_framework import serializers

from courses.models import Course, Tag, Chapter, Lesson, ProgrammingLanguage, Category, Review, BaseLessonStep
from users.api.serializers import LearnerSerializer
from .mixins import ValidateAllowedFieldsMixin
from .serializer_fields import ImageOrUrlField, LessonStepField
from .. import cache_utils
from ..factories import LessonStepFactory


logger = logging.getLogger(__name__)


class ProgrammingLanguageSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = ProgrammingLanguage
        fields = ['id', 'name']


class LessonSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    lesson_steps = LessonStepField(source='baselessonstep_set', required=False)
    chapter_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'order', 'title', 'chapter_id', 'lesson_steps']

    def validate(self, data):
        order = data.get('order')
        if order is not None and order <= 0:
            raise serializers.ValidationError({"order": "Order must be greater or equal to 1."})
        return data

    def create(self, validated_data):
        with transaction.atomic():
            lesson_steps_data = validated_data.pop('baselessonstep_set', [])
            lesson = Lesson.objects.create(**validated_data)

            for lesson_step_data in lesson_steps_data:
                LessonStepFactory.create(lesson_step_data, lesson)

        return lesson

    def update(self, instance, validated_data):
        with transaction.atomic():
            lesson_steps_data = validated_data.get('baselessonstep_set', [])
            if lesson_steps_data:
                # Delete the steps that aren't included in the request
                instance.baselessonstep_set.exclude(id__in=[step.id for step in lesson_steps_data]).delete()
            instance = super().update(instance, validated_data)

        return instance

    def get_chapter_id(self, obj):
        return obj.chapter.id


class ChapterSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    lessons = LessonSerializer(many=True, required=False)

    class Meta:
        model = Chapter
        fields = ['id', 'title', 'creation_date', 'lessons']

    def create(self, validated_data):
        with transaction.atomic():
            lessons_data = validated_data.pop('lessons', [])
            chapter = Chapter.objects.create(**validated_data)
            for lesson_data in lessons_data:
                lesson_serializer = LessonSerializer(data=lesson_data)
                if lesson_serializer.is_valid(raise_exception=True):
                    lesson_steps = lesson_data.pop('baselessonstep_set', [])
                    lesson_serializer.save(chapter=chapter, baselessonstep_set=lesson_steps)

        return chapter

    def update(self, instance, validated_data):
        with transaction.atomic():
            lessons_data = validated_data.pop('lessons', [])
            instance = super().update(instance, validated_data)
            lessons_ids_to_keep = []
            for lesson_data in lessons_data:
                try:
                    UUID(lesson_data['id'])
                except ValueError:
                    lesson_data.pop('id', None)
                    lesson_serializer = LessonSerializer(data=lesson_data)
                else:
                    lesson = Lesson.objects.get(id=lesson_data['id'])
                    lesson_serializer = LessonSerializer(lesson, data=lesson_data, partial=True)

                if lesson_serializer.is_valid(raise_exception=True):
                    lesson_instance = lesson_serializer.save(chapter=instance)
                    lessons_ids_to_keep.append(lesson_instance.id)
            instance.lesson_set.exclude(id__in=lessons_ids_to_keep).delete()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['lessons'] = LessonSerializer(instance.lesson_set.all(), many=True, context=self.context).data
        return representation


class TagSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class ReviewSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    learner = LearnerSerializer(many=False, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'learner', 'rating', 'comment', 'creation_date']


class CategorySerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = Category
        fields = ['id', 'name', 'supercategory']


class CategoryField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return cache_utils.get_categories()

    def to_representation(self, value):
        category = next((cat for cat in self.get_queryset() if cat.pk == value.pk), None)
        if category is not None:
            return CategorySerializer(category).data
        return None

    def to_internal_value(self, data):
        queryset = self.get_queryset()

        for instance in queryset:
            if str(instance.pk) == str(data):
                return instance

        # if not found in the cache, raise a validation error
        self.fail('does_not_exist', pk_value=data)


class CourseSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    tags = TagSerializer(many=True, required=False)
    chapters = ChapterSerializer(many=True, required=False)
    category = CategoryField(queryset=Category.objects.all(), required=False)
    image = ImageOrUrlField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'category', 'intro', 'description', 'requirements', 'total_hours', 'chapters',
                  'creation_date', 'release_date', 'price', 'image', 'tags', 'active', 'level']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['chapters'] = ChapterSerializer(instance.chapter_set.all(), many=True, context=self.context).data
        return representation

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        chapters_data = validated_data.pop('chapters', [])

        instance = super().update(instance, validated_data)

        if tags_data:
            tags = []
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(name=tag_data['name'])
                tags.append(tag)

            instance.tags.set(tags)

        if chapters_data:
            chapters_ids_to_keep = []
            with transaction.atomic():
                for chapter_data in chapters_data:
                    try:
                        UUID(chapter_data['id'])
                    except ValueError:
                        chapter_data.pop('id', None)
                        chapter_serializer = ChapterSerializer(data=chapter_data)
                    else:
                        try:
                            chapter = Chapter.objects.get(id=chapter_data['id'])
                        except Chapter.DoesNotExist:
                            raise serializers.ValidationError({'chapter': f'Chapter with id {chapter_data["id"]} does not exist.'})
                        chapter_serializer = ChapterSerializer(chapter, data=chapter_data, partial=True)

                    if chapter_serializer.is_valid(raise_exception=True):
                        lessons = chapter_data.pop('lessons', [])
                        chapter_instance = chapter_serializer.save(course=instance, lessons=lessons)
                        chapters_ids_to_keep.append(chapter_instance.id)

                # Delete chapters not in chapters_ids_to_keep
                instance.chapter_set.exclude(id__in=chapters_ids_to_keep).delete()

        return instance

    def create(self, validated_data):
        chapters_data = validated_data.pop('chapters', [])
        tags_data = validated_data.pop('tags', [])
        tag_names = [tag['name'] for tag in tags_data]

        with transaction.atomic():
            course = Course.objects.create(**validated_data)

            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                course.tags.add(tag)

            for chapter_data in chapters_data:
                chapter_serializer = ChapterSerializer(data=chapter_data)
                if chapter_serializer.is_valid(raise_exception=True):
                    lessons = chapter_data.pop('lessons', [])
                    chapter_serializer.save(course=course, lessons=lessons)

        return course
