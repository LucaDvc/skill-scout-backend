from uuid import UUID

from rest_framework.generics import GenericAPIView

from courses import cache_utils
from learning.api.serializers import LearnerProgressSerializer
from learning.models import LearnerProgress


class LearnerCourseViewMixin(GenericAPIView):
    """
    Mixin to add 'is_learner' key to the serializer context.
    """

    def get_serializer_context(self):
        """
        Adding 'is_learner' key to the serializer context.
        """
        context = super().get_serializer_context()
        context['is_learner'] = True
        return context

    def get_course_data(self, course):
        """
        Get course data from cache or db and attach learner progress.
        :param course: Course object
        :return: Serialized course data
        """
        course_data = cache_utils.get_learner_course_data(course)

        user = self.request.user
        learner_progress = LearnerProgress.objects.filter(learner=user, course=course).first()
        if learner_progress:
            course_data['learner_progress'] = LearnerProgressSerializer(learner_progress).data

        for chapter_rep in course_data['chapters']:
            chapter_rep['completed'] = UUID(chapter_rep['id']) in learner_progress.completed_chapters
            for lesson_rep in chapter_rep['lessons']:
                lesson_rep['completed'] = UUID(lesson_rep['id']) in learner_progress.completed_lessons
                for step_rep in lesson_rep['lesson_steps']:
                    step_rep['completed'] = UUID(step_rep['id']) in learner_progress.completed_steps

        return course_data
