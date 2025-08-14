# backend/payments/views.py
import stripe # type: ignore
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking
from .models import Payment
from .serializers import CreateIntentSerializer


class CreateIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        booking_id = s.validated_data["booking"]

        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        if booking.status == "canceled":
            return Response({"detail": "Booking canceled"}, status=status.HTTP_400_BAD_REQUEST)

        amount = booking.amount_cents
        currency = getattr(settings, "STRIPE_CURRENCY", "eur")

        # --- FREE FLOW : événements gratuits -> pas d'appel Stripe
        if amount <= 0:
            payment = Payment.objects.filter(booking=booking, status="succeeded").order_by("-created_at").first()
            if not payment:
                payment = Payment.objects.create(
                    user=request.user,
                    booking=booking,
                    amount_cents=0,
                    currency=currency,
                    status="succeeded",
                )
            if booking.status == "pending":
                booking.status = "confirmed"
                booking.save(update_fields=["status"])
            return Response({"client_secret": None, "payment_id": payment.id, "free": True}, status=status.HTTP_201_CREATED)

        # --- PAYANT : Stripe PaymentIntent
        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            return Response({"detail": "Stripe not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        payment = Payment.objects.filter(booking=booking, status="pending").order_by("-created_at").first()
        try:
            if payment and payment.stripe_payment_intent_id:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            else:
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    automatic_payment_methods={"enabled": True},
                    metadata={"booking_id": str(booking.id), "user_id": str(request.user.id)},
                )
                if payment is None:
                    payment = Payment.objects.create(
                        user=request.user,
                        booking=booking,
                        amount_cents=amount,
                        currency=currency,
                        stripe_payment_intent_id=intent["id"],
                        status="pending",
                    )
                else:
                    payment.stripe_payment_intent_id = intent["id"]
                    payment.amount_cents = amount
                    payment.currency = currency
                    payment.save(update_fields=["stripe_payment_intent_id", "amount_cents", "currency", "updated_at"])
        except stripe.error.StripeError as e:
            msg = getattr(e, "user_message", None) or str(e)
            return Response({"detail": f"stripe_error: {msg}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"client_secret": intent["client_secret"], "payment_id": payment.id}, status=status.HTTP_201_CREATED)



@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE")
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret:
            return Response({"detail": "Webhook secret not configured"}, status=500)
        try:
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=secret)
        except ValueError:
            return Response({"detail": "Invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({"detail": "Invalid signature"}, status=400)

        etype = event.get("type")
        obj = event["data"]["object"]
        if obj.get("object") != "payment_intent":
            return Response({"detail": "ignored"}, status=200)

        pi_id = obj["id"]
        new_status = None
        if etype == "payment_intent.succeeded":
            new_status = "succeeded"
        elif etype == "payment_intent.canceled":
            new_status = "canceled"
        elif etype == "payment_intent.payment_failed":
            new_status = "failed"

        if not new_status:
            return Response({"detail": "ignored"}, status=200)

        try:
            with transaction.atomic():
                payment = Payment.objects.select_related("booking").select_for_update().get(
                    stripe_payment_intent_id=pi_id
                )
                if payment.status != new_status:
                    payment.status = new_status
                    payment.amount_cents = int(obj.get("amount") or payment.amount_cents)
                    payment.save(update_fields=["status", "amount_cents", "updated_at"])

                    if new_status == "succeeded" and payment.booking.status == "pending":
                        b = payment.booking
                        b.status = "confirmed"
                        b.save(update_fields=["status"])
        except Payment.DoesNotExist:
            return Response({"detail": "payment not found (ok)"}, status=200)

        return Response({"detail": "ok"}, status=200)
