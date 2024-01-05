
# User is_private display logic
class PrivacyMixin:
    def to_representation(self, instance):
        if instance.is_private:
            return {
                'id': instance.id,
                'first_name': 'Anonymous',
                'last_name': str(instance.id)[:8]
            }
        return super().to_representation(instance)
