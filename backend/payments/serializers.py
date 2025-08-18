from rest_framework import serializers

class CreateIntentSerializer(serializers.Serializer):
    """
    Utilisé par la route 'réelle' /payments/create-intent/
    Accepte soit un booking_public_id (UUID), soit un booking (PK int).
    """
    booking_public_id = serializers.UUIDField(required=False)
    booking = serializers.IntegerField(required=False)
    return_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("booking_public_id") and not attrs.get("booking"):
            raise serializers.ValidationError("booking_public_id ou booking est requis.")
        return attrs


class ConfirmSimulatorSerializer(serializers.Serializer):
    """
    Utilisé par la route simulateur /payments/sim/confirm/ (tests .http)
    """
    booking_public_id = serializers.UUIDField()
    # 1) PaymentMethod test (pm_card_visa…) OU
    payment_method = serializers.CharField(required=False, allow_blank=True)
    # 2) Carte brute (si STRIPE_RAW_CARD_SIM_ENABLED)
    card_number = serializers.CharField(required=False, allow_blank=True)
    exp_month = serializers.IntegerField(required=False)
    exp_year = serializers.IntegerField(required=False)
    cvc = serializers.CharField(required=False, allow_blank=True)

    return_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, attrs):
        pm = attrs.get("payment_method")
        has_card = all(k in attrs and attrs[k] for k in ("card_number", "exp_month", "exp_year", "cvc"))
        if not pm and not has_card:
            raise serializers.ValidationError(
                "Fournir payment_method OU (card_number, exp_month, exp_year, cvc)."
            )
        return attrs
