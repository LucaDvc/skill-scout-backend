from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from courses.models import Course
from users.api.mixins import PrivacyMixin
from users.models import User


class SimpleProfileSerializer(PrivacyMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'is_private', 'short_bio', 'picture']


class ProfileCourseSerializer(serializers.ModelSerializer):
    enrolled_learners = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'total_hours', 'price', 'image', 'average_rating', 'enrolled_learners']

    def get_enrolled_learners(self, obj):
        return obj.enrolled_learners.count()


class DetailedProfileSerializer(PrivacyMixin, serializers.ModelSerializer):
    courses = ProfileCourseSerializer(many=True, read_only=True, source='course_set')

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'city', 'short_bio', 'about', 'picture', 'linked_in', 'facebook',
                  'personal_website', 'youtube', 'is_private', 'courses']


class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title']


class UserSerializer(serializers.ModelSerializer):
    wishlist = SimpleCourseSerializer(many=True, read_only=True)
    enrolled_courses = SimpleCourseSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'city', 'short_bio', 'about', 'picture', 'linked_in', 'facebook',
                  'personal_website', 'youtube', 'is_private', 'wishlist', 'enrolled_courses']


class LearnerSerializer(serializers.ModelSerializer):
    wishlist = SimpleCourseSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'city', 'short_bio', 'about', 'picture', 'linked_in', 'facebook',
                  'personal_website', 'youtube', 'is_private', 'wishlist']


class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'register_error': 'Password fields do not match'})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['email'],
            validated_data['password1'],
            validated_data['first_name'],
            validated_data['last_name']
        )
        user.save()
        return user


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    token = serializers.CharField(write_only=True, required=True)
    uidb64 = serializers.CharField(write_only=True, required=True)
