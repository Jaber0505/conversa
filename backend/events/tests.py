from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from languages.models import Language
from partners.models import Partner
from bookings.models import Booking, BookingStatus
from events.models import Event

User = get_user_model()


class EventFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@example.com", password="pass123456", age=21, consent_given=True)
        self.other = User.objects.create_user(email="v@example.com", password="pass123456", age=21, consent_given=True)
        self.lang = Language.objects.create(code="fr", name="Français")
        self.partner = Partner.objects.create(name="Bar Test", address="Rue 1", postal_code="1000", city="Bruxelles", country="BE")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_event_creates_pending_booking_for_organizer(self):
        url = reverse("event-list")
        payload = {
            "partner": self.partner.id,
            "language": self.lang.id,
            "theme": "Soirée FR",
            "difficulty": "easy",
            "datetime_start": "2999-12-31T20:00:00Z",
        }
        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, 201)
        ev_id = r.data["id"]
        ev = Event.objects.get(id=ev_id)
        self.assertEqual(ev.status, Event.Status.DRAFT)
        # booking organizer auto
        b = Booking.objects.get(event=ev, user=self.user)
        self.assertEqual(b.status, BookingStatus.PENDING)
        self.assertEqual(b.amount_cents, ev.price_cents)

    def test_list_shows_published_for_all_and_my_drafts(self):
        # Create my draft
        e1 = Event.objects.create(
            organizer=self.user, partner=self.partner, language=self.lang,
            theme="Draft", difficulty="easy", datetime_start="2999-12-31T20:00:00Z", status=Event.Status.DRAFT
        )
        # Create other's published
        e2 = Event.objects.create(
            organizer=self.other, partner=self.partner, language=self.lang,
            theme="Pub", difficulty="easy", datetime_start="2999-12-31T21:00:00Z", status=Event.Status.PUBLISHED
        )
        r = self.client.get(reverse("event-list"))
        ids = [x["id"] for x in r.data]
        self.assertIn(e1.id, ids)
        self.assertIn(e2.id, ids)

    def test_cancel_event_cascades_bookings(self):
        # Create event + a participant booking confirmed
        e = Event.objects.create(
            organizer=self.user, partner=self.partner, language=self.lang,
            theme="To cancel", difficulty="easy", datetime_start="2999-12-31T20:00:00Z", status=Event.Status.PUBLISHED
        )
        # organizer booking
        Booking.objects.create(user=self.user, event=e, amount_cents=e.price_cents, currency="EUR", status=BookingStatus.CONFIRMED)
        # someone else booking
        Booking.objects.create(user=self.other, event=e, amount_cents=e.price_cents, currency="EUR", status=BookingStatus.CONFIRMED)

        r = self.client.post(reverse("event-cancel", args=[e.id]), {}, format="json")
        self.assertEqual(r.status_code, 200)

        # all bookings cancelled
        self.assertFalse(Booking.objects.filter(event=e).exclude(status=BookingStatus.CANCELLED).exists())
