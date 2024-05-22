from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from courses.models import TextLessonStep, QuizLessonStep, QuizChoice, VideoLessonStep, \
    BaseLessonStep,  CodeChallengeTestCase, CodeChallengeLessonStep
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

    def create(self, validated_data):
        base_step_data = validated_data.pop('base_step')
        if isinstance(base_step_data, dict):
            base_step_data['lesson'] = self.context['lesson']
            base_step = BaseLessonStep.objects.create(**base_step_data)
        else:
            base_step = base_step_data
        text_step = TextLessonStep.objects.create(base_step=base_step, **validated_data)
        # Returning the base step instance to be used in the lesson serializer
        return base_step if isinstance(base_step_data, dict) else text_step

    # TODO copy paste in every step serializer
    def update(self, instance, validated_data):
        base_step_data = validated_data.pop('base_step')
        base_step = instance.base_step
        for attr, value in base_step_data.items():
            setattr(base_step, attr, value)
        base_step.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Returning the base step instance to be used in the lesson serializer
        return base_step


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


class QuizLessonStepSerializer(serializers.ModelSerializer, LessonStepSerializerMixin):
    quiz_choices = QuizChoiceSerializer(many=True, required=False)

    class Meta:
        model = QuizLessonStep
        fields = ['id', 'order', 'question', 'explanation', 'quiz_choices']

    def create(self, validated_data):
        base_step_data = validated_data.pop('base_step')
        if isinstance(base_step_data, dict):
            base_step_data['lesson'] = self.context['lesson']
            base_step = BaseLessonStep.objects.create(**base_step_data)
        else:
            base_step = base_step_data

        quiz_choices_data = validated_data.pop('quiz_choices', [])
        quiz_lesson_step = QuizLessonStep.objects.create(base_step=base_step, **validated_data)

        for quiz_choice_data in quiz_choices_data:
            # Remove the id field if it exists, as it's not needed when creating a new instance
            quiz_choice_data.pop('id', None)
            QuizChoice.objects.create(quiz=quiz_lesson_step, **quiz_choice_data)

        # Returning the base step instance to be used in the lesson serializer
        return base_step if isinstance(base_step_data, dict) else quiz_lesson_step

    def update(self, instance, validated_data):
        base_step_data = validated_data.pop('base_step')
        if base_step_data:
            base_step = instance.base_step
            for attr, value in base_step_data.items():
                setattr(base_step, attr, value)
            base_step.save()

        quiz_choices_data = validated_data.pop('quiz_choices', [])
        if quiz_choices_data is not None:
            instance.quizchoice_set.all().delete()  # Clear existing quiz choices
            for quiz_choice_data in quiz_choices_data:
                quiz_choice_data.pop('id', None)
                QuizChoice.objects.create(quiz=instance, **quiz_choice_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Returning the base step instance to be used in the lesson serializer
        return base_step if base_step_data else instance

    def to_representation(self, obj):
        representation = super().to_representation(obj)

        quiz_choices = obj.quizchoice_set.all()
        representation['quiz_choices'] = QuizChoiceSerializer(quiz_choices, many=True, context=self.context).data
        representation['type'] = 'quiz'
        correct_choices_count = len([choice for choice in quiz_choices if choice.correct])
        is_multiple_choice = correct_choices_count > 1
        representation['multiple_choice'] = is_multiple_choice

        return representation


class VideoLessonStepSerializer(serializers.ModelSerializer, LessonStepSerializerMixin):
    video_file = serializers.SerializerMethodField()

    class Meta:
        model = VideoLessonStep
        fields = ['id', 'order', 'title', 'video_file']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'video'
        return representation

    def get_video_file(self, obj):
        # Return the URL of the video file
        if obj.video_file:
            return obj.video_file.url
        return None

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH']:
            video_file = request.data.get('video_file')
            if video_file is None or video_file == '':
                # Remove the video file from the step
                attrs['video_file'] = None
            elif isinstance(video_file, str):
                # Validate if it's a URL
                url_validator = URLValidator()
                try:
                    url_validator(video_file)
                    # Check if the URL matches the existing video file URL
                    if self.instance and self.instance.video_file:
                        if video_file == self.instance.video_file.url:
                            # If URL matches, remove it from attrs to avoid update
                            attrs.pop('video_file', None)
                except ValidationError:
                    raise serializers.ValidationError({"video_file": "Invalid URL for video file."})
            elif hasattr(video_file, 'read'):
                # It's a file upload, keep it in attrs
                attrs['video_file'] = video_file
            else:
                raise serializers.ValidationError({"video_file": "Invalid data type for video file."})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        # Handle updating video step on lesson update, as well as specific video step update
        base_step_data = validated_data.pop('base_step', None)

        # If updating inside lesson, update base step
        if base_step_data:
            base_step = instance.base_step
            for attr, value in base_step_data.items():
                setattr(base_step, attr, value)
            base_step.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Returning the base step instance to be used in the lesson serializer
        return base_step if base_step_data else instance


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
        base_step_data = validated_data.pop('base_step')
        if isinstance(base_step_data, dict):
            base_step_data['lesson'] = self.context['lesson']
            base_step = BaseLessonStep.objects.create(**base_step_data)
        else:
            base_step = base_step_data

        test_cases_data = validated_data.pop('test_cases', [])

        language = validated_data.pop('language')
        language_id = language['id']
        validated_data['language'], _ = cache_utils.get_language_by_id(language_id)

        code_lesson_step = CodeChallengeLessonStep.objects.create(base_step=base_step, **validated_data)

        for test_case_data in test_cases_data:
            # Remove the id field if it exists, as it's not needed when creating a new instance
            test_case_data.pop('id', None)
            CodeChallengeTestCase.objects.create(code_challenge_step=code_lesson_step, **test_case_data)

        return base_step if isinstance(base_step_data, dict) else code_lesson_step

    def update(self, instance, validated_data):
        base_step_data = validated_data.pop('base_step', None)

        # If updating inside lesson, update base step
        if base_step_data:
            base_step = instance.base_step
            for attr, value in base_step_data.items():
                setattr(base_step, attr, value)
            base_step.save()

        test_cases_data = validated_data.pop('test_cases', None)
        language_data = validated_data.pop('language', None)

        if language_data:
            instance.language, _ = cache_utils.get_language_by_id(language_data['id'])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if test_cases_data is not None:
            instance.test_cases.all().delete()  # Clear existing test cases
            for test_case_data in test_cases_data:
                test_case_data.pop('id', None)
                CodeChallengeTestCase.objects.create(code_challenge_step=instance, **test_case_data)

        # Returning the base step instance to be used in the lesson serializer
        return base_step if base_step_data else instance

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation['test_cases'] = CodeChallengeTestCaseSerializer(obj.test_cases.all(), many=True, context=self.context).data
        representation['type'] = 'codechallenge'
        return representation
