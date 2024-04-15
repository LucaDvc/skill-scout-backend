from rest_framework import serializers

from courses.api.serializers import TagSerializer, CategoryField, ReviewSerializer
from courses.models import Course, Category, Chapter, Lesson
from users.api.serializers import SimpleProfileSerializer


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
    instructor = SimpleProfileSerializer(many=False, read_only=True)
    chapters = CatalogChaptersSerializer(many=True, read_only=True, source='chapter_set')
    level = serializers.CharField(source='get_level_display')

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'category', 'intro', 'description', 'requirements', 'level',
                  'total_hours', 'release_date', 'price', 'image', 'tags', 'average_rating', 'reviews',
                  'enrolled_learners', 'chapters']

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()


class SimpleCatalogCourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category = CategoryField(queryset=Category.objects.all())
    instructor = SimpleProfileSerializer(many=False, read_only=True)
    enrolled_learners = serializers.IntegerField(read_only=True, source='enrolled_learners_count')
    average_rating = serializers.FloatField(read_only=True, source='avg_rating')
    reviews_no = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField(method_name='get_is_enrolled')

    class Meta:
        model = Course
        fields = ['id', 'title', 'intro', 'instructor', 'category', 'level', 'total_hours', 'price', 'image', 'tags',
                  'average_rating', 'enrolled_learners', 'reviews_no', 'is_enrolled']

    def get_is_enrolled(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        else:
            return obj.enrolled_learners.filter(id=user.id).exists()


class CategoryListSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'top', 'subcategories']

    def get_subcategories(self, instance):
        subcategories = instance.subcategories.all()
        return CategoryListSerializer(subcategories, many=True, context=self.context).data
