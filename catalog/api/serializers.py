from rest_framework import serializers

from courses.api.serializers import TagSerializer, CategoryField, ReviewSerializer
from courses.models import Course, Category, Chapter, Lesson
from users.api.serializers import UserSerializer


class CatalogLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['order', 'title']


class CatalogChaptersSerializer(serializers.ModelSerializer):
    lessons = CatalogLessonSerializer(many=True, read_only=False, source='lesson_set')

    class Meta:
        model = Chapter
        fields = ['title', 'lessons']


class DetailedCatalogCourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category = CategoryField(queryset=Category.objects.all())
    reviews = ReviewSerializer(many=True, read_only=True, source='review_set')
    enrolled_learners = serializers.SerializerMethodField()
    instructor = UserSerializer(many=False, read_only=True)
    chapters = CatalogChaptersSerializer(many=True, read_only=True, source='chapter_set')

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'category', 'intro', 'description', 'requirements', 'total_hours',
                  'release_date', 'price', 'image', 'tags', 'average_rating', 'reviews', 'enrolled_learners', 'chapters']

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()


class SimpleCatalogCourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category = CategoryField(queryset=Category.objects.all())
    enrolled_learners = serializers.SerializerMethodField()
    instructor = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'category', 'total_hours', 'price', 'image', 'tags', 'average_rating',
                  'enrolled_learners']

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()

