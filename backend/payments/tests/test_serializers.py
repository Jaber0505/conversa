"""
Tests unitaires pour les serializers de Payments.

Objectif: valider la structure/validation des payloads sans dépendance réseau.
"""

from django.test import TestCase
from rest_framework import serializers

from payments.serializers import (
    CreateCheckoutSessionSerializer,
    CheckoutSessionCreatedSerializer,
    APIErrorSerializer,
    WebhookAckSerializer,
)


class CreateCheckoutSessionSerializerTest(TestCase):
    def test_valid_payload(self):
        data = {
            "booking_public_id": "6f9619ff-8b86-d011-b42d-00c04fc964ff",
            "lang": "fr",
            "success_url": "http://localhost:4200/fr/stripe/success",
            "cancel_url": "http://localhost:4200/fr/stripe/cancel",
        }
        ser = CreateCheckoutSessionSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_missing_booking_public_id(self):
        data = {"lang": "fr"}
        ser = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn("booking_public_id", ser.errors)

    def test_invalid_booking_public_id(self):
        data = {"booking_public_id": "not-a-uuid", "lang": "fr"}
        ser = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn("booking_public_id", ser.errors)

    def test_lang_required(self):
        data = {"booking_public_id": "6f9619ff-8b86-d011-b42d-00c04fc964ff"}
        ser = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn("lang", ser.errors)


class OtherSerializersTest(TestCase):
    def test_checkout_session_created_serializer(self):
        ser = CheckoutSessionCreatedSerializer(data={"url": "https://stripe.com", "session_id": "cs_123"})
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_api_error_serializer(self):
        ser = APIErrorSerializer(data={"detail": "msg", "code": "conflict"})
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_webhook_ack_serializer(self):
        ser = WebhookAckSerializer(data={"detail": "ok"})
        self.assertTrue(ser.is_valid(), ser.errors)
