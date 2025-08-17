
import pytest
from bookings.models import Booking, BookingStatus
from django.utils import timezone

pytestmark = pytest.mark.django_db

BASE = "/api/v1"

class DummyStripePI:
    def __init__(self, id="pi_test", client_secret="cs_test"):
        self.id = id
        self.client_secret = client_secret
    def __getitem__(self, k):
        return getattr(self, k)

def test_create_intent_paid_flow(api_client, user, event, monkeypatch, settings):
    api_client.force_authenticate(user=user)

    # Booking payable
    b = Booking.objects.create(
        user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        status=BookingStatus.PENDING,
    )

    # Patch Stripe
    created = DummyStripePI(id="pi_paid_1", client_secret="secret_1")
    def fake_create(**kwargs): return created
    def fake_retrieve(pi_id): return created
    import payments.views as pv
    monkeypatch.setattr(pv, "stripe", type("S", (), {"PaymentIntent": type("P", (), {"create": staticmethod(fake_create), "retrieve": staticmethod(fake_retrieve)}), "Webhook": object}))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")

    resp = api_client.post(f"{BASE}/payments/create-intent/", {"booking_public_id": str(b.public_id)}, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.data["client_secret"] == "secret_1"
    assert resp.data["payment_intent_id"] == "pi_paid_1"

def test_create_intent_free_confirms_immediately(api_client, user, free_event):
    api_client.force_authenticate(user=user)
    # Booking gratuit: amount_cents = 0
    from bookings.models import Booking
    b = Booking.objects.create(
        user=user, event=free_event, quantity=1, amount_cents=0, currency="EUR",
        status="PENDING"
    )
    resp = api_client.post(f"{BASE}/payments/create-intent/", {"booking_public_id": str(b.public_id)}, format="json")
    assert resp.status_code == 201
    assert resp.data["free"] is True
    b.refresh_from_db()
    assert b.status == "CONFIRMED"

def test_create_intent_ttl_returns_409(api_client, user, event):
    api_client.force_authenticate(user=user)
    b = Booking.objects.create(
        user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
        expires_at=timezone.now() - timezone.timedelta(minutes=1),
        status="PENDING"
    )
    resp = api_client.post(f"{BASE}/payments/create-intent/", {"booking_public_id": str(b.public_id)}, format="json")
    assert resp.status_code == 409
    b.refresh_from_db()
    assert b.status == "CANCELLED"
