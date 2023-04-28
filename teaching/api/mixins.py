from rest_framework import serializers


class ExtraFieldsValidationMixin():
    def validate(self, attrs):
        self.check_extra_fields(attrs)
        return attrs

    def check_extra_fields(self, attrs):
        model_fields = {f.name for f in self.__class__.Meta.model._meta.get_fields()}
        extra_fields = set(attrs.keys()) - model_fields

        if extra_fields:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in extra_fields}
            )


class StepTypeMixin(serializers.Serializer):
    type = serializers.SerializerMethodField(method_name='get_step_type')

    def get_step_type(self, obj):
        # Get the class name of the object and convert it to lowercase
        return obj.__class__.__name__.lower().replace("lessonstep", "")
