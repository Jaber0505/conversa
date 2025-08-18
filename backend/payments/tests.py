from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.test import override_settings
from events.models import Event
from languages.models import Language
from partners.models import Partner
from bookings.models import Booking, BookingStatus
from payments.models import Payment

User = get_user_model()

class PaymentSimulatorTests(APITestCase):
    def setUp(self):
        self.u = User.objects.create_user(email="u@example.com", password="pass123456", age=21, consent_given=True)
        self.client = APIClient()
        self.client.force_authenticate(self.u)

        self.lang = Language.objects.create(code="fr", name="Français")
        self.partner = Partner.objects.create(name="Lieu", address="Rue 1", postal_code="1000", city="Bruxelles", country="BE")
        self.event = Event.objects.create(
            organizer=self.u, partner=self.partner, language=self.lang,
            theme="EV", difficulty="easy", datetime_start="2999-12-31T20:00:00Z", status=Event.Status.DRAFT
        )
        self.booking = Booking.objects.create(user=self.u, event=self.event, amount_cents=700, currency="EUR")

    @override_settings(DJANGO_ENABLE_PAYMENT_SIMULATOR=True, STRIPE_SECRET_KEY="sk_test_xxx")
    def test_simulator_success_confirms_booking_and_publishes_event(self):
        # create-intent (facultatif ici, le simulateur le fera si nécessaire)
        _ = self.client.post(reverse("payments-create-intent"), {"booking_public_id": str(self.booking.public_id)}, format="json")

        res = self.client.post(reverse("payments-confirm-simulator"), {
            "booking_public_id": str(self.booking.public_id),
            "payment_method": "pm_card_visa"
        }, format="json")
        self.assertEqual(res.status_code, 200)

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.Status.PUBLISHED)

        p = Payment.objects.filter(booking=self.booking).latest("id")
        self.assertEqual(p.status, "succeeded")
