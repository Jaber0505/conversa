from rest_framework import serializers

class CreateCheckoutSessionSerializer(serializers.Serializer):
    booking_public_id = serializers.UUIDField(help_text="UUID public de la réservation")
    lang = serializers.CharField(required=True, allow_blank=True, max_length=16, help_text="Segment langue (ex: fr)")
    success_url = serializers.URLField(required=False, help_text="URL de succès (override)")
    cancel_url  = serializers.URLField(required=False, help_text="URL d'annulation (override)")

class CheckoutSessionCreatedSerializer(serializers.Serializer):
    url = serializers.URLField(help_text="URL Stripe Checkout à ouvrir")
    session_id = serializers.CharField(allow_null=True, required=False, help_text="ID de la session Checkout (cs_...)")

class APIErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Message d'erreur lisible")
    code = serializers.CharField(required=False, help_text="Code d'erreur technique (optionnel)")

class WebhookAckSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text='Toujours "ok" si l’événement a été accusé')
