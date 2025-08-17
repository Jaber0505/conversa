
import pytest
from bookings.models import Booking, BookingStatus
from payments.models import Payment
from django.utils import timezone

pytestmark = pytest.mark.django_db

BASE = "/api/v1"

def _post_webhook(api_client, event_dict, monkeypatch):
    import payments.views as pv
    class DummyWebhook:
        @staticmethod
        def construct_event(payload, sig_header, secret):
            return event_dict
    # monkeypatch only the Webhook with our dummy
    monkeypatch.setattr(pv, "stripe", type("S", (), {"Webhook": DummyWebhook}))

    # Send any body/signature; construct_event ignores them now
    return api_client.post(f"{BASE}/payments/stripe-webhook/", data=b"{}", content_type="application/json")

def test_webhook_succeeded_updates_booking_and_payment(api_client, user, event, monkeypatch):
    api_client.force_authenticate(user=user)
    b = Booking.objects.create(
        user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
        status="PENDING", expires_at=timezone.now() + timezone.timedelta(minutes=10)
    )
    p = Payment.objects.create(user=user, booking=b, amount_cents=700, currency="EUR",
                               stripe_payment_intent_id="pi_succ", status="pending")

    evt = {"type": "payment_intent.succeeded", "data": {"object": {
        "object": "payment_intent", "id": "pi_succ", "amount": 700,
        "metadata": {"booking_public_id": str(b.public_id)}
    }}}

    resp = _post_webhook(api_client, evt, monkeypatch)
    assert resp.status_code == 200
    b.refresh_from_db(); p.refresh_from_db()
    assert b.status == "CONFIRMED"
    assert p.status == "succeeded"

def test_webhook_failed_cancels_booking(api_client, user, event, monkeypatch):
    api_client.force_authenticate(user=user)
    b = Booking.objects.create(user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
                               status="PENDING")
    p = Payment.objects.create(user=user, booking=b, amount_cents=700, currency="EUR",
                               stripe_payment_intent_id="pi_fail", status="pending")
    evt = {"type": "payment_intent.payment_failed", "data": {"object": {
        "object": "payment_intent", "id": "pi_fail", "amount": 700, "metadata": {"booking_public_id": str(b.public_id)}
    }}}
    resp = _post_webhook(api_client, evt, monkeypatch)
    assert resp.status_code == 200
    b.refresh_from_db(); p.refresh_from_db()
    assert b.status == "CANCELLED"
    assert p.status == "failed"

def test_webhook_canceled_cancels_booking(api_client, user, event, monkeypatch):
    api_client.force_authenticate(user=user)
    b = Booking.objects.create(user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
                               status="PENDING")
    p = Payment.objects.create(user=user, booking=b, amount_cents=700, currency="EUR",
                               stripe_payment_intent_id="pi_cancel", status="pending")
    evt = {"type": "payment_intent.canceled", "data": {"object": {
        "object": "payment_intent", "id": "pi_cancel", "amount": 700, "metadata": {"booking_public_id": str(b.public_id)}
    }}}
    resp = _post_webhook(api_client, evt, monkeypatch)
    assert resp.status_code == 200
    b.refresh_from_db(); p.refresh_from_db()
    assert b.status == "CANCELLED"
    assert p.status == "canceled"

def test_webhook_fallback_by_metadata_when_payment_missing(api_client, user, event, monkeypatch):
    api_client.force_authenticate(user=user)
    b = Booking.objects.create(user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
                               status="PENDING")
    # No Payment in DB. Webhook should still confirm via metadata fallback.
    evt = {"type": "payment_intent.succeeded", "data": {"object": {
        "object": "payment_intent", "id": "pi_unknown", "amount": 700, "metadata": {"booking_public_id": str(b.public_id)}
    }}}
    resp = _post_webhook(api_client, evt, monkeypatch)
    assert resp.status_code == 200
    b.refresh_from_db()
    assert b.status == "CONFIRMED"
