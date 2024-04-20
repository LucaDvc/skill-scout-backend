from django.db.models import Count, Sum
from rest_framework import serializers

from courses.api.serializers import CourseSerializer, ReviewSerializer
from learning.models import LearnerProgress, CodeChallengeSubmission, TestResult
from uuid import UUID

from users.api.serializers import SimpleProfileSerializer


class LearnerProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProgress
        fields = ['last_stopped_chapter', 'last_stopped_lesson', 'last_stopped_step',
                  'completed_chapters', 'completed_lessons', 'completed_steps', 'completion_ratio']


class LearnerCourseSerializer(CourseSerializer):
    learner_progress = serializers.SerializerMethodField()
    instructor = SimpleProfileSerializer(many=False, read_only=True)
    enrolled_learners = serializers.SerializerMethodField()
    level = serializers.CharField(source='get_level_display')
    lessons_count = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = (CourseSerializer.Meta.fields +
                  ['learner_progress', 'average_rating', 'instructor', 'enrolled_learners', 'level', 'lessons_count'])

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()

    def fetch_learner_progress(self, course):
        user = self.context['request'].user
        try:
            learner_progress = LearnerProgress.objects.get(learner=user, course=course)
        except LearnerProgress.DoesNotExist:
            return None

        return learner_progress

    def get_learner_progress(self, course):
        learner_progress = self.fetch_learner_progress(course)
        return LearnerProgressSerializer(learner_progress).data if learner_progress else None

    def get_lessons_count(self, course):
        return course.chapter_set.annotate(
            lessons_count=Count('lesson')
        ).aggregate(
            total=Sum('lessons_count')
        )['total']

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        learner_progress = self.fetch_learner_progress(instance)
        if not learner_progress:
            return rep

        # add 'completed' field to each child object and assign the values according to learner_progress
        for chapter_rep in rep['chapters']:
            chapter_rep['completed'] = UUID(chapter_rep['id']) in learner_progress.completed_chapters
            for lesson_rep in chapter_rep['lessons']:
                lesson_rep['completed'] = UUID(lesson_rep['id']) in learner_progress.completed_lessons
                for step_rep in lesson_rep['lesson_steps']:
                    step_rep['completed'] = UUID(step_rep['id']) in learner_progress.completed_steps

        return rep


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
