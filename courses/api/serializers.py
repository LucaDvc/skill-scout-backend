from rest_framework import serializers
from courses.models import Course, Tag, Chapter, Lesson, TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep, \
    BaseLessonStep
from .mixins import LessonStepSerializerMixin


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


class BaseLessonStepSerializer(BaseModelSerializer):
    class Meta:
        model = BaseLessonStep
        fields = ['id', 'order']


class TextLessonStepSerializer(BaseModelSerializer, LessonStepSerializerMixin):
    class Meta:
        model = TextLessonStep
        fields = ['id', 'type', 'order', 'text']


class QuizChoiceSerializer(BaseModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ['id', 'text', 'correct']


class QuizLessonStepSerializer(BaseModelSerializer, LessonStepSerializerMixin):
    quiz_choices = QuizChoiceSerializer(many=True, required=False)

    class Meta:
        model = QuizLessonStep
        fields = ['id', 'type', 'order', 'question', 'explanation', 'quiz_choices']

    def create(self, validated_data):
        quiz_choices_data = validated_data.pop('quiz_choices', [])
        quiz_lesson_step = QuizLessonStep.objects.create(**validated_data)

        for quiz_choice_data in quiz_choices_data:
            QuizChoice.objects.create(quiz=quiz_lesson_step, **quiz_choice_data)

        return quiz_lesson_step

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation['quiz_choices'] = QuizChoiceSerializer(obj.quizchoice_set.all(), many=True).data
        return representation


class VideoLessonStepSerializer(BaseModelSerializer, LessonStepSerializerMixin):
    class Meta:
        model = VideoLessonStep
        fields = ['id', 'order', 'title', 'video_file']


class LessonSerializer(BaseModelSerializer):
    lesson_steps = serializers.SerializerMethodField()
    chapter_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'order', 'title', 'chapter_id', 'lesson_steps']

    def validate(self, data):
        order = data.get('order')
        if order is not None and order <= 0:
            raise serializers.ValidationError({"order": "Order must be greater or equal to 1."})
        return data

    def get_lesson_steps(self, obj):
        all_steps = BaseLessonStep.objects.filter(lesson=obj)
        serialized_steps = []
        for step in all_steps:
            if hasattr(step, 'text_step'):
                serialized_steps.append(TextLessonStepSerializer(step.text_step).data)
            elif hasattr(step, 'quiz_step'):
                serialized_steps.append(QuizLessonStepSerializer(step.quiz_step).data)
            elif hasattr(step, 'video_step'):
                serialized_steps.append(VideoLessonStepSerializer(step.video_step).data)

        ordered_steps = sorted(serialized_steps, key=lambda x: x['order'])

        return ordered_steps

    def get_chapter_id(self, obj):
        return obj.chapter.id


class ChapterSerializer(BaseModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = ['id', 'title', 'creation_date', 'lessons']

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
        fields = ['id', 'title', 'intro', 'description', 'requirements', 'total_hours', 'chapters',
                  'creation_date', 'release_date', 'price', 'image', 'tags', 'active']

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])

        instance = super().update(instance, validated_data)

        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_data['name'])
            instance.tags.add(tag)

        return instance

    def get_chapters(self, obj):
        return ChapterSerializer(obj.chapter_set.all(), many=True, required=False).data