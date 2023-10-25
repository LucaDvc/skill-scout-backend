from rest_framework.generics import GenericAPIView


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
