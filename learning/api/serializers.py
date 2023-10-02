from rest_framework import serializers

from courses.api.serializers import CourseSerializer
from learning.models import LearnerProgress, CodeChallengeSubmission, TestResult


class LearnerCourseSerializer(CourseSerializer):
    learner_progress = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['learner_progress']

    def get_learner_progress(self, obj):
        learner_progress_list = self.context.get('learner_progress_list', [])
        matching_progress = next((progress for progress in learner_progress_list if progress.course.id == obj.id), None)
        if matching_progress:
            return LearnerProgressSerializer(matching_progress).data
        return None


class LearnerProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProgress
        fields = ['last_stopped_chapter', 'last_stopped_lesson', 'last_stopped_step',
                  'completed_chapters', 'completed_lessons', 'completed_steps', 'completion_ratio']


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
