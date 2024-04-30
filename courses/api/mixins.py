from rest_framework import serializers


class LessonStepTypeField(serializers.Field):
    def to_representation(self, obj):
        # Return the type based on the class name of the object
        return obj.__class__.__name__.lower().replace("lessonstep", "")

    def to_internal_value(self, data):
        # Simply return the type value as it is, as we're handling the creation in the factory
        return data


class LessonStepSerializerMixin(serializers.Serializer):
    id = serializers.UUIDField(source='base_step.id', read_only=True)
    order = serializers.IntegerField(source='base_step.order', required=False)
    type = LessonStepTypeField()

    def validate(self, data):
        if data.get('order') is not None and data.get('order') <= 0:
            raise serializers.ValidationError({"order": "Order must be greater or equal to 1."})
        return data


class ValidateAllowedFieldsMixin:
    def to_internal_value(self, data):
        allowed_fields = set(self.Meta.fields)
        extra_fields = set(data.keys()) - allowed_fields

        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )

        return super().to_internal_value(data)
