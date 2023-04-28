from rest_framework import serializers
from courses.models import Course, Tag, Chapter, Lesson, TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep
from .mixins import StepTypeMixin


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = '__all__'

    def to_internal_value(self, data):
        allowed_fields = set(self.Meta.fields)
        extra_fields = set(data.keys()) - allowed_fields

        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )

        return super().to_internal_value(data)


class TextLessonStepSerializer(BaseModelSerializer, StepTypeMixin):
    class Meta:
        model = TextLessonStep
        fields = '__all__'


class QuizChoiceSerializer(BaseModelSerializer):
    class Meta:
        model = QuizChoice
        exclude = ['quiz']


class QuizLessonStepSerializer(BaseModelSerializer, StepTypeMixin):
    quiz_choices = QuizChoiceSerializer(many=True)

    class Meta:
        model = QuizLessonStep
        fields = '__all__'


class VideoLessonStepSerializer(BaseModelSerializer, StepTypeMixin):
    class Meta:
        model = VideoLessonStep
        fields = '__all__'


class LessonSerializer(BaseModelSerializer):
    lesson_steps = serializers.SerializerMethodField()
    chapter_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'order', 'title', 'chapter_id', 'lesson_steps']

    def get_lesson_steps(self, obj):
        text_steps = TextLessonStepSerializer(obj.textlessonstep_set.all(), many=True).data
        quiz_steps = QuizLessonStepSerializer(obj.quizlessonstep_set.all(), many=True).data
        video_steps = VideoLessonStepSerializer(obj.videolessonstep_set.all(), many=True).data

        all_steps = text_steps + quiz_steps + video_steps
        ordered_steps = sorted(all_steps, key=lambda x: x['order'])

        return ordered_steps

    def get_chapter_id(self, obj):
        return obj.chapter.id


class ChapterSerializer(BaseModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        exclude = ['course']

    def get_lessons(self, obj):
        return LessonSerializer(obj.lesson_set.all(), many=True, required=False).data


class TagSerializer(BaseModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class CourseSerializer(BaseModelSerializer):
    tags = TagSerializer(many=True, required=False)
    chapters = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['instructor']

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])

        instance = super().update(instance, validated_data)

        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_data['name'])
            instance.tags.add(tag)

        return instance

    def get_chapters(self, obj):
        return ChapterSerializer(obj.chapter_set.all(), many=True).data
