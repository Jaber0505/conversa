
import pytest
from django.utils import timezone
from bookings.models import Booking, BookingStatus

pytestmark = pytest.mark.django_db

BASE = "/api/v1"

def test_booking_create_list_detail_cancel(api_client, user, event):
    api_client.force_authenticate(user=user)

    # Create
    resp = api_client.post(f"{BASE}/bookings/", {"event": event.id, "quantity": 1}, format="json")
    assert resp.status_code == 201, resp.content
    public_id = resp.data["public_id"]

    # List
    resp = api_client.get(f"{BASE}/bookings/")
    assert resp.status_code == 200
    data = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
    assert any(b["public_id"] == public_id for b in data)

    # Detail
    resp = api_client.get(f"{BASE}/bookings/{public_id}/")
    assert resp.status_code == 200
    assert resp.data["status"] == "PENDING"

    # Cancel
    resp = api_client.post(f"{BASE}/bookings/{public_id}/cancel/")
    assert resp.status_code == 200
    assert resp.data["status"] == "CANCELLED"

def test_booking_ttl_autocancel_on_list(api_client, user, event):
    api_client.force_authenticate(user=user)
    # Create directly with past expiry
    b = Booking.objects.create(
        user=user, event=event, quantity=1, amount_cents=700, currency="EUR",
        expires_at=timezone.now() - timezone.timedelta(minutes=1),
        status=BookingStatus.PENDING,
    )
    # Listing triggers soft-cancel of expired PENDING
    resp = api_client.get(f"{BASE}/bookings/")
    assert resp.status_code == 200
    # refresh
    b.refresh_from_db()
    assert b.status == BookingStatus.CANCELLED
