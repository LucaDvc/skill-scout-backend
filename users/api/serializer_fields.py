from rest_framework import serializers
import os
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile


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
