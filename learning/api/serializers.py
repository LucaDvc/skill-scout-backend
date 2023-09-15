from rest_framework import serializers

from courses.api.serializers import CourseSerializer
from learning.models import LearnerProgress


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
