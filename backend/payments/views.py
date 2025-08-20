import re
import stripe
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import (
    extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
)

from rest_framework import status, views
from rest_framework.response import Response

from common.permissions import IsAuthenticatedAndActive as AuthPerm  # permission projet

from .serializers import (
    CreateCheckoutSessionSerializer,
    CheckoutSessionCreatedSerializer,
    APIErrorSerializer,
    WebhookAckSerializer,
)

from .models import Payment
from bookings.models import Booking, BookingStatus


# --- helpers --------------------------------------------------------------

def _require_test_key_or_500():
    """Charge la clé Stripe TEST et échoue sinon."""
    key = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        raise RuntimeError("Stripe TEST uniquement : STRIPE_SECRET_KEY doit commencer par 'sk_test_'.")
    stripe.api_key = key
    return key

def _with_leading_slash(p: str, default: str) -> str:
    p = (p or default).strip()
    return p if p.startswith("/") else "/" + p

def _front_base() -> str:
    return getattr(settings, "FRONTEND_BASE_URL", "http://localhost:4200").rstrip("/")

def _build_return_urls(lang: str, booking_public_id: str, success_override: str | None, cancel_override: str | None):
    if success_override and cancel_override:
        success_url = success_override
        cancel_url  = cancel_override
    else:
        success_path = _with_leading_slash(getattr(settings, "STRIPE_SUCCESS_PATH", "/stripe/success"), "/stripe/success")
        cancel_path  = _with_leading_slash(getattr(settings, "STRIPE_CANCEL_PATH",  "/stripe/cancel"),  "/stripe/cancel")
        base = _front_base()
        success_url = f"{base}/{lang}{success_path}"
        cancel_url  = f"{base}/{lang}{cancel_path}"

    qs = {"b": str(booking_public_id), "lang": lang}
    success_url = f"{success_url}?{urlencode(qs)}&cs={{CHECKOUT_SESSION_ID}}"
    cancel_url  = f"{cancel_url}?{urlencode(qs)}"
    return success_url, cancel_url


# --- endpoints ------------------------------------------------------------

class CreateCheckoutSessionView(views.APIView):
    """
    Crée une session Stripe Checkout (TEST) et renvoie l'URL Stripe.
    Appelée par le front.
    """
    permission_classes = [AuthPerm]
    
    @extend_schema(
        tags=["Payments"],
        operation_id="payments_create_checkout_session",
        summary="Créer une session Stripe Checkout (TEST) et renvoyer l'URL",
        request=CreateCheckoutSessionSerializer,
        responses={
            201: OpenApiResponse(CheckoutSessionCreatedSerializer, description="Session créée"),
            401: OpenApiResponse(APIErrorSerializer, description="Non authentifié"),
            403: OpenApiResponse(APIErrorSerializer, description="Utilisateur inactif"),
            404: OpenApiResponse(APIErrorSerializer, description="Booking introuvable"),
            409: OpenApiResponse(APIErrorSerializer, description="Booking expirée ou non payable"),
            502: OpenApiResponse(APIErrorSerializer, description="Erreur Stripe"),
        },
        examples=[
            OpenApiExample(
                "Requête minimale",
                value={"booking_public_id": "11111111-1111-1111-1111-111111111111", "lang": "fr"},
                request_only=True,
            ),
            OpenApiExample(
                "Réponse 201",
                value={"url": "https://checkout.stripe.com/c/pay/cs_test_abc123", "session_id": "cs_test_abc123"},
                response_only=True,
            ),
            OpenApiExample(
                "Conflit 409 (booking expirée)",
                value={"detail": "Réservation expirée."},
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def post(self, request):
        ser = CreateCheckoutSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        booking = get_object_or_404(Booking, public_id=ser.validated_data["booking_public_id"], user=request.user)

        # Vérifs métier
        if hasattr(booking, "soft_cancel_if_expired") and booking.soft_cancel_if_expired():
            return Response({"detail": "Réservation expirée."}, status=status.HTTP_409_CONFLICT)
        if booking.status != BookingStatus.PENDING:
            return Response({"detail": "Réservation non payable."}, status=status.HTTP_409_CONFLICT)

        # Langue (string libre) nettoyée
        lang = re.sub(r"[^A-Za-z\-]", "", (ser.validated_data.get("lang") or "")).strip() or "fr"

        # URLs de retour
        success_url, cancel_url = _build_return_urls(
            lang=lang,
            booking_public_id=str(booking.public_id),
            success_override=ser.validated_data.get("success_url"),
            cancel_override=ser.validated_data.get("cancel_url"),
        )

        # Montant 0 → bypass Stripe : confirme + trace Payment
        if int(getattr(booking, "amount_cents", 0)) <= 0:
            with transaction.atomic():
                if hasattr(booking, "mark_confirmed"):
                    booking.mark_confirmed()
                else:
                    booking.status = BookingStatus.CONFIRMED
                    booking.save(update_fields=["status"])
                Payment.objects.create(
                    user=request.user,
                    booking=booking,
                    amount_cents=int(getattr(booking, "amount_cents", 0)),
                    currency=(getattr(booking, "currency", None) or getattr(settings, "STRIPE_CURRENCY", "eur")).upper(),
                    status="succeeded",
                )
            return Response({"url": success_url, "session_id": None}, status=status.HTTP_201_CREATED)

        # Stripe Checkout (TEST)
        _require_test_key_or_500()
        currency = (getattr(booking, "currency", None) or getattr(settings, "STRIPE_CURRENCY", "eur")).lower()

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "unit_amount": int(booking.amount_cents),
                        "product_data": {"name": getattr(getattr(booking, "event", None), "title", "Conversa – Session")},
                    },
                    "quantity": int(getattr(booking, "quantity", 1)),
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=getattr(request.user, "email", None) or None,
                client_reference_id=str(booking.public_id),
                metadata={"booking_public_id": str(booking.public_id), "user_id": str(request.user.id)},
                payment_intent_data={"metadata": {"booking_public_id": str(booking.public_id), "user_id": str(request.user.id)}},
                # idempotency key: peut être passée via options requête ; on s'appuie ici sur la contrainte côté DB/booking
            )
        except stripe.error.StripeError as e:
            return Response({"detail": getattr(e, "user_message", None) or str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Trace Payment (pending)
        Payment.objects.update_or_create(
            booking=booking,
            user=request.user,
            defaults=dict(
                stripe_checkout_session_id=session.id,
                amount_cents=int(booking.amount_cents),
                currency=currency.upper(),
                status="pending",
            ),
        )

        return Response({"url": session.url, "session_id": session.id}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(views.APIView):
    """
    Webhook Stripe (TEST) : confirme la réservation sur checkout.session.completed.
    Appelé par Stripe (public), signature vérifiée.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Payments"],
        operation_id="payments_stripe_webhook",
        summary="Webhook Stripe (TEST) — reçoit les événements de paiement",
        description=(
            "Endpoint public appelé par Stripe. Vérifie la signature `Stripe-Signature`.\n\n"
            "- `checkout.session.completed` ➜ confirme la booking, met à jour le Payment\n"
            "- `payment_intent.payment_failed` ➜ marque le Payment en `failed`\n"
            "- `checkout.session.expired` ➜ marque la session `canceled` (optionnel)\n"
        ),
        parameters=[
            OpenApiParameter(
                name="Stripe-Signature",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Signature Stripe du webhook"
            ),
        ],
        request=None,  # payload JSON Stripe (variable)
        responses={
            200: OpenApiResponse(WebhookAckSerializer, description='ACK de l’événement ({"detail":"ok"})'),
            400: OpenApiResponse(APIErrorSerializer, description="Signature/payload invalide"),
            500: OpenApiResponse(APIErrorSerializer, description="Webhook secret manquant côté serveur"),
        },
        examples=[
            OpenApiExample(
                "Extrait — checkout.session.completed",
                value={
                    "type": "checkout.session.completed",
                    "data": {"object": {
                        "id": "cs_test_abc123",
                        "payment_intent": "pi_3XYZ...",
                        "client_reference_id": "11111111-1111-1111-1111-111111111111",
                        "metadata": {"booking_public_id": "11111111-1111-1111-1111-111111111111"}
                    }}
                },
                request_only=True,
            ),
            OpenApiExample(
                "Réponse OK",
                value={"detail": "ok"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        if not secret:
            return Response({"detail": "Webhook secret missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(payload=request.body, sig_header=sig, secret=secret)
        except Exception:
            return Response({"detail": "invalid signature/payload"}, status=status.HTTP_400_BAD_REQUEST)

        etype = event.get("type")
        data = event.get("data", {}).get("object", {})

        # Succès de Checkout
        if etype == "checkout.session.completed":
            public_id = (data.get("metadata") or {}).get("booking_public_id") or data.get("client_reference_id")
            session_id = data.get("id")
            payment_intent_id = data.get("payment_intent")

            if public_id:
                with transaction.atomic():
                    try:
                        booking = Booking.objects.select_for_update().get(public_id=public_id)
                    except Booking.DoesNotExist:
                        return Response({"detail": "ok"}, status=200)

                    # Confirme la booking si encore en attente
                    if booking.status == BookingStatus.PENDING:
                        if hasattr(booking, "mark_confirmed"):
                            booking.mark_confirmed()
                        else:
                            booking.status = BookingStatus.CONFIRMED
                            booking.save(update_fields=["status"])

                    # Trace Payment
                    pay, _ = Payment.objects.get_or_create(
                        booking=booking,
                        user=getattr(booking, "user", None),
                        defaults=dict(
                            amount_cents=int(getattr(booking, "amount_cents", 0)),
                            currency=(getattr(booking, "currency", None) or getattr(settings, "STRIPE_CURRENCY", "eur")).upper(),
                            status="pending",
                        ),
                    )
                    if session_id:
                        pay.stripe_checkout_session_id = pay.stripe_checkout_session_id or session_id
                    if payment_intent_id:
                        pay.stripe_payment_intent_id = pay.stripe_payment_intent_id or payment_intent_id
                    pay.status = "succeeded"
                    pay.raw_event = data
                    pay.save()

        # Échec de PaymentIntent (si reçu séparément)
        elif etype == "payment_intent.payment_failed":
            pi = data.get("id")
            if pi:
                Payment.objects.filter(stripe_payment_intent_id=pi).update(status="failed")

        # Session expirée (optionnel: marquer "canceled")
        elif etype == "checkout.session.expired":
            sid = data.get("id")
            if sid:
                Payment.objects.filter(stripe_checkout_session_id=sid, status="pending").update(status="canceled")

        return Response({"detail": "ok"}, status=200)
