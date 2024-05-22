from django.db.models import Count, Sum
from rest_framework import serializers

from courses.api.serializers import CourseSerializer, ReviewSerializer
from learning.models import LearnerProgress, CodeChallengeSubmission, TestResult
from uuid import UUID

from users.api.serializers import SimpleProfileSerializer


class LearnerProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProgress
        fields = ['last_stopped_lesson', 'last_stopped_step', 'completed_chapters', 'completed_lessons', 'completed_steps', 'completion_ratio']


class LearnerCourseSerializer(CourseSerializer):
    instructor = SimpleProfileSerializer(many=False, read_only=True)
    enrolled_learners = serializers.SerializerMethodField()
    level = serializers.CharField(source='get_level_display')
    lessons_count = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = (CourseSerializer.Meta.fields +
                  ['average_rating', 'instructor', 'enrolled_learners', 'level', 'lessons_count'])

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()

    def get_lessons_count(self, course):
        return course.chapter_set.annotate(
            lessons_count=Count('lesson')
        ).aggregate(
            total=Sum('lessons_count')
        )['total']

    def to_representation(self, instance):
        return super().to_representation(instance)


class TestResultSerializer(serializers.ModelSerializer):
    input = serializers.CharField(source='test_case.input', read_only=True)
    expected_output = serializers.CharField(source='test_case.expected_output', read_only=True)

    class Meta:
        model = TestResult
        fields = ['input', 'expected_output', 'stdout', 'stderr', 'compile_err', 'status', 'passed']


class CodeChallengeSubmissionSerializer(serializers.ModelSerializer):
    test_results = TestResultSerializer(many=True, read_only=True)
    code_challenge_id = serializers.UUIDField(source='code_challenge_step.base_step.id', read_only=True)
    learner_id = serializers.UUIDField(source='learner.id', read_only=True)

    class Meta:
        model = CodeChallengeSubmission
        fields = ['code_challenge_id', 'learner_id', 'submitted_code', 'passed', 'error_message', 'test_results']

# TODO review serializer and crud endpoint
