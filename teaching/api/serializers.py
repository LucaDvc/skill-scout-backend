from rest_framework import serializers
from learning.models import CourseEnrollment
from users.api.serializers import LearnerSerializer


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    learner = LearnerSerializer(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ['learner', 'active', 'completed', 'favourite', 'enrolled_at']
