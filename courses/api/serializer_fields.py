import uuid

from rest_framework import serializers
import os
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile

from courses.api.lesson_steps_serializers import TextLessonStepSerializer, VideoLessonStepSerializer, \
    CodeChallengeLessonStepSerializer, QuizLessonStepSerializer
from courses.models import TextLessonStep, QuizLessonStep, VideoLessonStep, CodeChallengeLessonStep


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
                serializer = TextLessonStepSerializer(item.text_step, context=self.context)
            elif hasattr(item, 'quiz_step'):
                serializer = QuizLessonStepSerializer(item.quiz_step, context=self.context)
            elif hasattr(item, 'video_step'):
                serializer = VideoLessonStepSerializer(item.video_step, context=self.context)
            elif hasattr(item, 'code_challenge_step'):
                serializer = CodeChallengeLessonStepSerializer(item.code_challenge_step, context=self.context)
            else:
                raise Exception('Unknown step type')

            result.append(serializer.data)
        return result

    def to_internal_value(self, data):
        # Convert incoming data to a list of lesson step instances
        steps = []
        for item in data:
            step_type = item.get('type')
            step_id = item.get('id', None)

            if step_type == 'text':
                serializer_class = TextLessonStepSerializer
                model_class = TextLessonStep
            elif step_type == 'quiz':
                serializer_class = QuizLessonStepSerializer
                model_class = QuizLessonStep
            elif step_type == 'video':
                serializer_class = VideoLessonStepSerializer
                model_class = VideoLessonStep
            elif step_type == 'codechallenge':
                serializer_class = CodeChallengeLessonStepSerializer
                model_class = CodeChallengeLessonStep
            else:
                raise serializers.ValidationError('Unknown step type')

            if step_id:
                try:
                    uuid.UUID(step_id, version=4)
                except ValueError:
                    # If it's not a valid uuid, create a new instance
                    serializer = serializer_class(data=item, context=self.context)
                else:
                    # If it's a valid uuid, update the existing instance
                    step_instance = model_class.objects.get(base_step_id=step_id)
                    serializer = serializer_class(step_instance, data=item)
            else:
                serializer = serializer_class(data=item, context=self.context)
            serializer.is_valid(raise_exception=True)
            step_instance = serializer.save()  # This save will either create or update the instance
            steps.append(step_instance)

        print('return ' + str(steps))

        return steps
