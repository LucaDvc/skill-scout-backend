from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from courses.models import Course
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'city', 'short_bio', 'about', 'picture', 'linked_in', 'facebook',
                  'personal_website', 'youtube']


class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title']


class LearnerSerializer(serializers.ModelSerializer):
    wishlist = SimpleCourseSerializer(many=True, read_only=True)
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'wishlist']


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
