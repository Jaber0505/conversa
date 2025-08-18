from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
from .models import Booking, BookingStatus

User = get_user_model()


class BookingFlowTests(APITestCase):
    def setUp(self):
        self.u = User.objects.create_user(
            email="u@example.com", password="pass123456", age=21, consent_given=True
        )
        self.v = User.objects.create_user(
            email="v@example.com", password="pass123456", age=21, consent_given=True
        )
        self.event = Event.objects.create(title="EV", price_cents=700, currency="EUR")
        self.client = APIClient()
        self.client.force_authenticate(self.u)

    def test_create_then_block_if_confirmed(self):
        r1 = self.client.post("/api/v1/bookings/", {"event": self.event.id}, format="json")
        self.assertEqual(r1.status_code, 201)
        b = Booking.objects.get(public_id=r1.data["public_id"])
        b.mark_confirmed()

        r2 = self.client.post("/api/v1/bookings/", {"event": self.event.id}, format="json")
        self.assertEqual(r2.status_code, 400)

    def test_list_is_scoped(self):
        self.client.post("/api/v1/bookings/", {"event": self.event.id}, format="json")
        # booking d'un autre user
        Booking.objects.create(user=self.v, event=self.event, amount_cents=700, currency="EUR")
        res = self.client.get("/api/v1/bookings/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(all(item["user"] == self.u.id for item in res.data))

    def test_expire_pending_on_list_and_cancel_pending_only(self):
        r = self.client.post("/api/v1/bookings/", {"event": self.event.id}, format="json")
        b = Booking.objects.get(public_id=r.data["public_id"])
        # force expiration
        b.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        b.save(update_fields=["expires_at"])

        # list => doit auto-canceller
        _ = self.client.get("/api/v1/bookings/")
        b.refresh_from_db()
        self.assertEqual(b.status, BookingStatus.CANCELLED)

        # cancel via DELETE sur déjà CANCELLED => 204
        res = self.client.delete(f"/api/v1/bookings/{b.public_id}/")
        self.assertEqual(res.status_code, 204)
