import stripe  # type: ignore
from uuid import UUID
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from bookings.models import Booking, BookingStatus
from .models import Payment
from .serializers import CreateIntentSerializer, ConfirmIntentSerializer
from common.permissions import IsAuthenticatedAndActive


def _get_setting(name: str, fallback: str = "") -> str:
    return getattr(settings, name, "") or getattr(settings, name.replace("DJANGO_", ""), fallback)

def _is_uuid(v: str) -> bool:
    try:
        UUID(str(v)); return True
    except Exception:
        return False

def _truthy(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"1","true","yes","y","on"}
    return False


@extend_schema(
    summary="Créer ou réutiliser un PaymentIntent pour une réservation",
    request=CreateIntentSerializer,
    responses={
        201: OpenApiResponse(
            description="Intent créé/réutilisé",
            examples=[OpenApiExample("paying", value={"client_secret": "pi_..._secret_...", "payment_id": 123})]
        ),
        201: OpenApiResponse(
            description="Gratuit",
            examples=[OpenApiExample("free", value={"free": True, "client_secret": None, "payment_id": 456})]
        ),
        409: OpenApiResponse(description="Reservation expired or not payable."),
        400: OpenApiResponse(description="Validation error"),
        500: OpenApiResponse(description="Stripe not configured"),
    },
    tags=["Payments"],
)
class CreateIntentView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        ident = s.validated_data.get("booking_public_id") or s.validated_data.get("booking")
        if _is_uuid(str(ident)):
            booking = get_object_or_404(Booking, public_id=ident, user=request.user)
        else:
            booking = get_object_or_404(Booking, pk=ident, user=request.user)

        # booking payable ?
        if booking.soft_cancel_if_expired() or booking.status != BookingStatus.PENDING:
            return Response({"detail": "Reservation expired or not payable."}, status=409)

        amount = int(booking.amount_cents)
        currency = booking.currency
        stripe_currency = currency.lower()

        # gratuit => confirmation immédiate
        if amount <= 0:
            payment = Payment.objects.filter(booking=booking, status="succeeded").order_by("-created_at").first()
            if not payment:
                payment = Payment.objects.create(
                    user=request.user, booking=booking, amount_cents=0, currency=currency, status="succeeded"
                )
            if booking.status == BookingStatus.PENDING:
                booking.mark_confirmed(late=booking.is_expired)
            return Response({"client_secret": None, "payment_id": payment.id, "free": True}, status=201)

        secret_key = _get_setting("DJANGO_STRIPE_SECRET_KEY")
        if not secret_key:
            return Response({"detail": "Stripe not configured"}, status=500)
        stripe.api_key = secret_key

        payment = Payment.objects.filter(booking=booking, status="pending").order_by("-created_at").first()
        intent = None
        try:
            if payment and payment.stripe_payment_intent_id:
                tmp = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                amd = (tmp.get("automatic_payment_methods") or {})
                # si ancien PI avec allow_redirects != "never", on remplace
                if amd.get("allow_redirects") == "never":
                    intent = tmp
                else:
                    try:
                        stripe.PaymentIntent.cancel(tmp["id"])
                    except stripe.error.StripeError:
                        pass
                    intent = None

            if intent is None:
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=stripe_currency,
                    # clé: pas de redirections => pas de return_url requis
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                    metadata={"booking_public_id": str(booking.public_id), "user_id": str(request.user.id)},
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

            # pratique pour debug: garder une trace sur la booking
            if booking.payment_intent_id != intent["id"]:
                booking.payment_intent_id = intent["id"]
                booking.save(update_fields=["payment_intent_id", "updated_at"])

        except stripe.error.StripeError as e:
            msg = getattr(e, "user_message", None) or str(e)
            return Response({"detail": f"stripe_error: {msg}"}, status=400)

        return Response(
            {"client_secret": intent["client_secret"], "payment_id": payment.id, "payment_intent_id": intent["id"]},
            status=201,
        )


@extend_schema(
    summary="(TEST) Confirmer le PaymentIntent côté serveur (simulateur front)",
    request=ConfirmIntentSerializer,
    responses={
        200: OpenApiResponse(
            description="Confirmation effectuée",
            examples=[OpenApiExample("ok", value={"payment_intent_status": "succeeded", "booking_status": "CONFIRMED"})]
        ),
        403: OpenApiResponse(description="Simulateur désactivé ou clés live"),
        409: OpenApiResponse(description="Booking expirée / non payable / pas d'intent"),
        400: OpenApiResponse(description="Erreur Stripe / validation"),
        500: OpenApiResponse(description="Stripe non configuré"),
    },
    tags=["Payments"],
)
class ConfirmIntentView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        # garde-fou: uniquement si flag actif ET clés test
        if not _truthy(getattr(settings, "STRIPE_CONFIRM_SIMULATOR_ENABLED", False)):
            return Response({"detail": "Simulateur désactivé."}, status=403)

        secret_key = _get_setting("DJANGO_STRIPE_SECRET_KEY")
        if not secret_key:
            return Response({"detail": "Stripe not configured"}, status=500)
        if not str(secret_key).startswith("sk_test_"):
            return Response({"detail": "Interdit avec des clés live."}, status=403)
        stripe.api_key = secret_key

        s = ConfirmIntentSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        booking = s.validated_data["__booking"]

        # état payable ?
        if booking.soft_cancel_if_expired() or booking.status != BookingStatus.PENDING:
            return Response({"detail": "Reservation expired or not payable."}, status=409)

        payment = Payment.objects.filter(booking=booking).order_by("-created_at").first()
        pi_id = payment.stripe_payment_intent_id if payment else booking.payment_intent_id
        if not pi_id:
            return Response({"detail": "Aucun PaymentIntent. Appelle d'abord /payments/create-intent/."}, status=409)

        payment_method = s.validated_data.get("payment_method") or "pm_card_visa"

        try:
            intent = stripe.PaymentIntent.confirm(pi_id, payment_method=payment_method)
        except stripe.error.StripeError as e:
            msg = getattr(e, "user_message", None) or str(e)
            return Response({"detail": f"stripe_error: {msg}"}, status=400)

        # Sync immédiate (en plus du webhook)
        with transaction.atomic():
            if payment:
                payment = Payment.objects.select_for_update().get(pk=payment.pk)
            booking.refresh_from_db()

            status_pi = intent["status"]
            if status_pi == "succeeded":
                if booking.status == BookingStatus.PENDING:
                    booking.mark_confirmed(late=booking.is_expired)
                if payment and payment.status != "succeeded":
                    payment.status = "succeeded"
                    payment.amount_cents = int(intent.get("amount") or payment.amount_cents)
                    payment.save(update_fields=["status", "amount_cents", "updated_at"])
            elif status_pi in ("canceled", "requires_payment_method"):
                # canceled -> annule ; requires_payment_method -> pas de changement booking
                if status_pi == "canceled" and booking.status == BookingStatus.PENDING:
                    booking.mark_cancelled()
                if payment and payment.status != status_pi:
                    payment.status = status_pi
                    payment.save(update_fields=["status", "updated_at"])
            # requires_action/processing -> laisser PENDING et laisser le webhook finaliser si besoin

        return Response({"payment_intent_status": intent["status"], "booking_status": booking.status}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
@extend_schema(
    summary="Stripe webhook (PaymentIntent events)",
    request=None,
    responses={200: OpenApiResponse(description="ok / ignored / not found")},
    tags=["Payments"],
)
class StripeWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE")
        secret = _get_setting("DJANGO_STRIPE_WEBHOOK_SECRET")
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
        metadata = obj.get("metadata") or {}
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
                try:
                    payment = Payment.objects.select_related("booking").select_for_update().get(
                        stripe_payment_intent_id=pi_id
                    )
                    booking = payment.booking
                except Payment.DoesNotExist:
                    booking = None
                    pub = metadata.get("booking_public_id")
                    if pub:
                        booking = Booking.objects.select_for_update().filter(public_id=pub).first()
                    if not booking:
                        return Response({"detail": "payment not found (ok)"}, status=200)

                if new_status in ("failed", "canceled"):
                    if booking.status == BookingStatus.PENDING:
                        booking.mark_cancelled()
                    if 'payment' in locals() and payment.status != new_status:
                        payment.status = new_status
                        payment.amount_cents = int(obj.get("amount") or payment.amount_cents)
                        payment.save(update_fields=["status", "amount_cents", "updated_at"])
                    return Response({"detail": "ok"}, status=200)

                if booking.status == BookingStatus.PENDING:
                    booking.mark_confirmed(late=booking.is_expired)
                if 'payment' in locals() and payment.status != "succeeded":
                    payment.status = "succeeded"
                    payment.amount_cents = int(obj.get("amount") or payment.amount_cents)
                    payment.save(update_fields=["status", "amount_cents", "updated_at"])

        except Exception:
            # idempotent-friendly
            return Response({"detail": "ok"}, status=200)

        return Response({"detail": "ok"}, status=200)
