import stripe  # type: ignore
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from bookings.models import Booking, BookingStatus
from payments.models import Payment
from payments.serializers import CreateIntentSerializer, ConfirmSimulatorSerializer
from common.permissions import IsAuthenticatedAndActive


# ---------- helpers

def _get_setting(name: str, fallback: str | None = None):
    """
    Cherche d'abord settings.<name>, puis settings.<name sans 'DJANGO_'>.
    Exemple: _get_setting('DJANGO_STRIPE_SECRET_KEY') prendra DJANGO_STRIPE_SECRET_KEY ou STRIPE_SECRET_KEY.
    """
    return getattr(settings, name, None) or getattr(settings, name.replace("DJANGO_", ""), fallback)

def _is_uuid(v: str) -> bool:
    try:
        UUID(str(v))
        return True
    except Exception:
        return False

def _maybe_publish_event_if_organizer_booking(booking: Booking):
    """
    Si le booking appartient à l'organisateur de l'évènement, on publie l'évènement.
    - Event.status DRAFT/AWAITING_PAYMENT -> PUBLISHED
    - Pas d'effet si déjà publié/annulé.
    """
    try:
        ev = booking.event
        if getattr(ev, "organizer_id", None) == booking.user_id and getattr(ev, "mark_published", None):
            ev.mark_published()
    except Exception:
        pass


# ---------- endpoints

@extend_schema(
    summary="Clé publishable Stripe (front)",
    responses={200: OpenApiResponse(description="OK")},
    tags=["Payments"],
)
class StripeConfigView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, _request):
        pk = _get_setting("DJANGO_STRIPE_PUBLISHABLE_KEY") or _get_setting("STRIPE_PUBLISHABLE_KEY")
        if not pk:
            return Response({"detail": "Stripe publishable key missing"}, status=500)
        cur = (_get_setting("DJANGO_STRIPE_CURRENCY") or _get_setting("STRIPE_CURRENCY") or "EUR").lower()
        return Response({"publishable_key": pk, "currency": cur}, status=200)


@extend_schema(
    summary="Créer / réutiliser un PaymentIntent pour une réservation (Payment Element)",
    request=CreateIntentSerializer,
    responses={
        201: OpenApiResponse(
            description="Intent créé/réutilisé",
            examples=[OpenApiExample("paying", value={"client_secret": "pi_..._secret_...", "payment_id": 123, "payment_intent_id": "pi_..."})]
        ),
        201: OpenApiResponse(description="Gratuit", examples=[OpenApiExample("free", value={"free": True, "client_secret": None, "payment_id": 456})]),
        409: OpenApiResponse(description="Reservation expired or not payable."),
        400: OpenApiResponse(description="Validation error"),
        500: OpenApiResponse(description="Stripe not configured"),
    },
    tags=["Payments"],
)
class CreateIntentView(APIView):
    """
    Route 'réelle' utilisée par le front (dev/prod).
    Accepte booking_public_id (UUID) OU booking (PK int).
    """
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        ident = s.validated_data.get("booking_public_id") or s.validated_data.get("booking")
        if _is_uuid(str(ident)):
            booking = get_object_or_404(Booking, public_id=ident, user=request.user)
        else:
            booking = get_object_or_404(Booking, pk=ident, user=request.user)

        # TTL & statut
        if booking.soft_cancel_if_expired() or booking.status != BookingStatus.PENDING:
            return Response({"detail": "Reservation expired or not payable."}, status=409)

        amount = int(booking.amount_cents)
        currency = (booking.currency or _get_setting("STRIPE_CURRENCY") or "EUR").upper()
        stripe_currency = currency.lower()

        # Gratuit => on confirme immédiatement (pas d’intent Stripe)
        if amount <= 0:
            payment = Payment.objects.filter(booking=booking, status="succeeded").order_by("-created_at").first()
            if not payment:
                payment = Payment.objects.create(
                    user=request.user, booking=booking, amount_cents=0, currency=currency, status="succeeded"
                )
            if booking.status == BookingStatus.PENDING:
                booking.mark_confirmed(late=booking.is_expired)
                _maybe_publish_event_if_organizer_booking(booking)
            return Response({"client_secret": None, "payment_id": payment.id, "free": True}, status=201)

        secret_key = _get_setting("DJANGO_STRIPE_SECRET_KEY") or _get_setting("STRIPE_SECRET_KEY")
        if not secret_key:
            return Response({"detail": "Stripe not configured"}, status=500)
        stripe.api_key = secret_key

        allow_redirects = _get_setting("STRIPE_PI_ALLOW_REDIRECTS") or "always"

        payment = Payment.objects.filter(booking=booking, status="pending").order_by("-created_at").first()
        try:
            if payment and payment.stripe_payment_intent_id:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            else:
                # Compatible Payment Element
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=stripe_currency,
                    automatic_payment_methods={"enabled": True, "allow_redirects": allow_redirects},
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
            # Miroir optionnel côté Booking
            if not getattr(booking, "payment_intent_id", None):
                booking.payment_intent_id = intent["id"]
                booking.save(update_fields=["payment_intent_id", "updated_at"])
        except stripe.error.StripeError as e:
            msg = getattr(e, "user_message", None) or str(e)
            return Response({"detail": f"stripe_error: {msg}"}, status=400)

        return Response(
            {"client_secret": intent["client_secret"], "payment_id": payment.id, "payment_intent_id": intent["id"]},
            status=201
        )


@extend_schema(
    summary="Simulateur unique (.http) : confirme un PaymentIntent",
    request=ConfirmSimulatorSerializer,
    responses={200: OpenApiResponse(description="OK"), 403: OpenApiResponse(description="Simulateur désactivé.")},
    tags=["Payments"],
)
class ConfirmSimulatorView(APIView):
    """
    Route 'simulateur' réservée à tes tests .http.
    Aucune variable d'env requise. Auth obligatoire.
    """
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        s = ConfirmSimulatorSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        booking = get_object_or_404(Booking, public_id=s.validated_data["booking_public_id"], user=request.user)
        if booking.soft_cancel_if_expired() or booking.status != BookingStatus.PENDING:
            return Response({"detail": "Reservation expired or not payable."}, status=409)

        secret_key = _get_setting("DJANGO_STRIPE_SECRET_KEY") or _get_setting("STRIPE_SECRET_KEY")
        if not secret_key:
            return Response({"detail": "Stripe not configured"}, status=500)
        stripe.api_key = secret_key

        # Récupère ou crée un PI
        payment = Payment.objects.filter(booking=booking, status="pending").order_by("-created_at").first()
        if payment and payment.stripe_payment_intent_id:
            pi_id = payment.stripe_payment_intent_id
        else:
            ci = CreateIntentView()
            ci.request = request
            resp = ci.post(request)
            if resp.status_code != 201 or not resp.data.get("payment_intent_id"):
                return Response({"detail": "Unable to build payment intent"}, status=400)
            pi_id = resp.data["payment_intent_id"]
            payment = Payment.objects.filter(booking=booking, status="pending").order_by("-created_at").first()

        # Choix PaymentMethod
        pm = s.validated_data.get("payment_method")
        if not pm and (_get_setting("DJANGO_STRIPE_RAW_CARD_SIM_ENABLED") or _get_setting("STRIPE_RAW_CARD_SIM_ENABLED")):
            try:
                pm_obj = stripe.PaymentMethod.create(
                    type="card",
                    card={
                        "number": s.validated_data["card_number"],
                        "exp_month": s.validated_data["exp_month"],
                        "exp_year": s.validated_data["exp_year"],
                        "cvc": s.validated_data["cvc"],
                    },
                )
                pm = pm_obj["id"]
            except stripe.error.StripeError as e:
                msg = getattr(e, "user_message", None) or str(e)
                return Response({"detail": f"stripe_error: {msg}"}, status=400)
        if not pm:
            pm = "pm_card_visa"

        return_url = s.validated_data.get("return_url") or \
                     _get_setting("STRIPE_CONFIRM_RETURN_URL_DEFAULT") or \
                     request.build_absolute_uri("/api/v1/payments/ok/")

        try:
            intent = stripe.PaymentIntent.confirm(pi_id, payment_method=pm, return_url=return_url)
        except stripe.error.StripeError as e:
            msg = getattr(e, "user_message", None) or str(e)
            with transaction.atomic():
                if booking.status == BookingStatus.PENDING:
                    booking.mark_cancelled()
                if payment and payment.status != "failed":
                    payment.status = "failed"
                    payment.save(update_fields=["status", "updated_at"])
            return Response({"detail": f"stripe_error: {msg}", "status": intent.status if 'intent' in locals() else "failed"}, status=400)

        if intent["status"] == "succeeded":
            with transaction.atomic():
                if booking.status == BookingStatus.PENDING:
                    booking.mark_confirmed(late=booking.is_expired)
                    _maybe_publish_event_if_organizer_booking(booking)
                if payment and payment.status != "succeeded":
                    payment.status = "succeeded"
                    payment.amount_cents = int(intent.get("amount") or payment.amount_cents or 0)
                    payment.save(update_fields=["status", "amount_cents", "updated_at"])
        elif intent["status"] in ("requires_action", "processing"):
            pass
        elif intent["status"] in ("requires_payment_method", "canceled"):
            with transaction.atomic():
                if booking.status == BookingStatus.PENDING:
                    booking.mark_cancelled()
                if payment and payment.status != intent["status"]:
                    payment.status = "failed" if intent["status"] == "requires_payment_method" else "canceled"
                    payment.save(update_fields=["status", "updated_at"])

        return Response({"detail": "ok", "payment_intent": intent}, status=200)


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
        secret = _get_setting("DJANGO_STRIPE_WEBHOOK_SECRET") or _get_setting("STRIPE_WEBHOOK_SECRET")
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
                payment = Payment.objects.select_related("booking").select_for_update().filter(
                    stripe_payment_intent_id=pi_id
                ).first()
                booking = payment.booking if payment else None
                if not booking:
                    pub = metadata.get("booking_public_id")
                    if pub:
                        booking = Booking.objects.select_for_update().filter(public_id=pub).first()
                    if not booking:
                        return Response({"detail": "payment not found (ok)"}, status=200)

                # échec/annulation
                if new_status in ("failed", "canceled"):
                    if booking.status == BookingStatus.PENDING:
                        booking.mark_cancelled()
                    if payment and payment.status != new_status:
                        payment.status = new_status
                        payment.amount_cents = int(obj.get("amount") or payment.amount_cents or 0)
                        payment.save(update_fields=["status", "amount_cents", "updated_at"])
                    return Response({"detail": "ok"}, status=200)

                # succès
                if booking.status == BookingStatus.PENDING:
                    booking.mark_confirmed(late=booking.is_expired)
                    _maybe_publish_event_if_organizer_booking(booking)
                if payment and payment.status != "succeeded":
                    payment.status = "succeeded"
                    payment.amount_cents = int(obj.get("amount") or payment.amount_cents or 0)
                    payment.save(update_fields=["status", "amount_cents", "updated_at"])
        except Exception:
            # On évite de retourner 500 (re-livraisons Stripe inutiles)
            return Response({"detail": "ok"}, status=200)

        return Response({"detail": "ok"}, status=200)
