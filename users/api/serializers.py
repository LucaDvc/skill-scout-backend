from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from users.models import User, Instructor


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class InstructorSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = Instructor
        fields = '__all__'


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

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'register_error': 'Password fields do not match'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['email'],
            validated_data['password1'],
            validated_data['first_name'],
            validated_data['last_name']
        )
        user.save()
        return user
