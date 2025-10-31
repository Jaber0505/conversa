from rest_framework import serializers

class CreateCheckoutSessionSerializer(serializers.Serializer):
    booking_public_id = serializers.UUIDField(help_text="Booking public UUID")
    lang = serializers.CharField(required=True, allow_blank=True, max_length=16, help_text="Language segment (e.g., fr)")
    success_url = serializers.URLField(required=False, help_text="Success URL (override)")
    cancel_url  = serializers.URLField(required=False, help_text="Cancel URL (override)")

class CheckoutSessionCreatedSerializer(serializers.Serializer):
    url = serializers.URLField(help_text="Stripe Checkout URL to redirect to")
    session_id = serializers.CharField(allow_null=True, required=False, help_text="Checkout session ID (cs_...)")

class APIErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Human-readable error message")
    code = serializers.CharField(required=False, help_text="Technical error code (optional)")

class WebhookAckSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text='Always "ok" if event was acknowledged')
