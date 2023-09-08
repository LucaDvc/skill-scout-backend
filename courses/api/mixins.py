from rest_framework import serializers


class LessonStepSerializerMixin(serializers.Serializer):
    type = serializers.SerializerMethodField(method_name='get_step_type')

    def get_step_type(self, obj):
        # Get the class name of the object and convert it to lowercase
        return obj.__class__.__name__.lower().replace("lessonstep", "")

    def validate(self, data):
        if data.get('order') is not None and data.get('order') <= 0:
            raise serializers.ValidationError({"order": "Order must be greater or equal to 1."})
        return data
