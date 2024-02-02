from rest_framework import serializers
import os
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile

from courses.api.lesson_steps_serializers import TextLessonStepSerializer, VideoLessonStepSerializer, \
    CodeChallengeLessonStepSerializer, QuizLessonStepSerializer


class ImageOrUrlField(serializers.Field):
    def to_internal_value(self, data):
        if isinstance(data, str):
            # Assuming it's a URL
            response = requests.get(data)
            if response.status_code == 200:
                parsed_url = urlparse(data)
                filename = os.path.basename(parsed_url.path)
                return ContentFile(response.content, name=filename)
            else:
                raise serializers.ValidationError("Unable to fetch image from URL")
        elif hasattr(data, 'read'):
            # It's a file upload
            return data
        else:
            raise serializers.ValidationError("Invalid data type for image")

    def to_representation(self, value):
        if value and hasattr(value, 'url'):
            # Return the URL path of the image
            return value.url
        return None


class LessonStepField(serializers.ListField):
    def to_representation(self, data):
        iterable = data.all() if hasattr(data, 'all') else data
        result = []
        for item in iterable:
            # Determine which serializer to use based on the step type
            if hasattr(item, 'text_step'):
                serializer = TextLessonStepSerializer(item.text_step)
            elif hasattr(item, 'quiz_step'):
                serializer = QuizLessonStepSerializer(item.quiz_step)
            elif hasattr(item, 'video_step'):
                serializer = VideoLessonStepSerializer(item.video_step)
            elif hasattr(item, 'code_challenge_step'):
                serializer = CodeChallengeLessonStepSerializer(item.code_challenge_step)
            else:
                raise Exception('Unknown step type')

            result.append(serializer.data)
        return result

    def to_internal_value(self, data):
        # Convert incoming data to a list of lesson step instances
        steps = []
        for item in data:
            step_type = item.get('type')
            if step_type == 'text':
                serializer = TextLessonStepSerializer(data=item)
            elif step_type == 'quiz':
                serializer = QuizLessonStepSerializer(data=item)
            elif step_type == 'video':
                serializer = VideoLessonStepSerializer(data=item)
            elif step_type == 'codechallenge':
                serializer = CodeChallengeLessonStepSerializer(data=item)
            else:
                raise serializers.ValidationError('Unknown step type')

            serializer.is_valid(raise_exception=True)
            serializer.validated_data['type'] = step_type
            steps.append(serializer.validated_data)

        return steps



