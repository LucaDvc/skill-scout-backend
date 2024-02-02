from courses.models import Course, Tag, Chapter, Lesson, TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep, \
    BaseLessonStep, ProgrammingLanguage, CodeChallengeTestCase, CodeChallengeLessonStep, Category, Review
from rest_framework import serializers
from .mixins import LessonStepSerializerMixin, ValidateAllowedFieldsMixin
from .. import cache_utils


class BaseLessonStepSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = BaseLessonStep
        fields = ['id', 'order']


class TextLessonStepSerializer(serializers.ModelSerializer, LessonStepSerializerMixin):
    class Meta:
        model = TextLessonStep
        fields = ['id', 'order', 'text']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'text'
        return representation


class QuizChoiceSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = QuizChoice
        fields = ['id', 'text', 'correct']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # If the user is viewing the course as a learner, remove the 'correct' field from the response
        if self.context.get('is_learner'):
            representation.pop('correct', None)

        return representation


class QuizLessonStepSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin, LessonStepSerializerMixin):
    quiz_choices = QuizChoiceSerializer(many=True, required=False)

    class Meta:
        model = QuizLessonStep
        fields = ['id', 'order', 'question', 'explanation', 'quiz_choices']

    def create(self, validated_data):
        quiz_choices_data = validated_data.pop('quiz_choices', [])
        quiz_lesson_step = QuizLessonStep.objects.create(**validated_data)

        for quiz_choice_data in quiz_choices_data:
            QuizChoice.objects.create(quiz=quiz_lesson_step, **quiz_choice_data)

        return quiz_lesson_step

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation['quiz_choices'] = QuizChoiceSerializer(obj.quizchoice_set.all(), many=True, context=self.context).data
        representation['type'] = 'quiz'
        return representation


class VideoLessonStepSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin, LessonStepSerializerMixin):
    class Meta:
        model = VideoLessonStep
        fields = ['id', 'order', 'title', 'video_file']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'video'
        return representation


class CodeChallengeTestCaseSerializer(serializers.ModelSerializer, ValidateAllowedFieldsMixin):
    class Meta:
        model = CodeChallengeTestCase
        fields = ['id', 'input', 'expected_output']


class CodeChallengeLessonStepSerializer(serializers.ModelSerializer,
                                        LessonStepSerializerMixin):
    language_id = serializers.IntegerField(source='language.id')
    test_cases = CodeChallengeTestCaseSerializer(many=True, required=False)

    class Meta:
        model = CodeChallengeLessonStep
        fields = ['id', 'order', 'title', 'description', 'language_id', 'initial_code', 'proposed_solution',
                  'test_cases']

    def create(self, validated_data):
        test_cases_data = validated_data.pop('test_cases', [])

        language = validated_data.pop('language')
        language_id = language['id']
        validated_data['language'], _ = cache_utils.get_language_by_id(language_id)

        code_lesson_step = CodeChallengeLessonStep.objects.create(**validated_data)

        for test_case_data in test_cases_data:
            CodeChallengeTestCase.objects.create(code_challenge_step=code_lesson_step, **test_case_data)

        return code_lesson_step

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation['test_cases'] = CodeChallengeTestCaseSerializer(obj.test_cases.all(), many=True, context=self.context).data
        representation['type'] = 'codechallenge'
        return representation
