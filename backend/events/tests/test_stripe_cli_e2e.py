"""
Stripe CLI end-to-end test for Events: pay-and-publish flow (opt-in).

This test exercises the event endpoint that creates an organizer booking and a
Stripe Checkout Session, then uses the Stripe CLI to trigger the webhook which
confirms the booking and publishes the event.

It is SKIPPED by default. Enable with:
  - RUN_STRIPE_CLI_TESTS=1
  - STRIPE_CLI_BIN=<absolute path to stripe CLI binary>

Run with ports exposed so the LiveServer is reachable by the CLI:

docker compose -f docker/compose.dev.yml run --rm --service-ports \
  -e DJANGO_SETTINGS_MODULE=config.settings.dev \
  -e RUN_STRIPE_CLI_TESTS=1 \
  -e STRIPE_CLI_BIN=/host_mnt/c/Users/<you>/Github/Conversa/conversa/backend/stripe.exe \
  backend python manage.py test events.tests.test_stripe_cli_e2e -v 2
"""

import os
import time
import subprocess
from unittest import skipUnless
from unittest.mock import patch, MagicMock

from django.test import LiveServerTestCase
from django.urls import reverse


# Bind LiveServer to a stable reachable port for Stripe CLI
os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "0.0.0.0:8000")


def _has_cli_enabled() -> bool:
    return os.getenv("RUN_STRIPE_CLI_TESTS") == "1"


def _cli_path() -> str | None:
    p = os.getenv("STRIPE_CLI_BIN")
    return p if p and os.path.exists(p) else None


@skipUnless(_has_cli_enabled() and _cli_path(), "Stripe CLI E2E disabled or CLI not found")
class EventsStripeCliE2ETest(LiveServerTestCase):
    databases = {"default"}

    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        from languages.models import Language
        from partners.models import Partner
        from events.models import Event

        User = get_user_model()

        # Organizer
        self.user = User.objects.create_user(
            email="organizer@example.com",
            password="pass12345",
            age=25,
            consent_given=True,
        )

        # Force-auth API client
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Language & Partner
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )
        self.partner = Partner.objects.create(
            name="E2E Venue",
            address="1 Rue Test",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Event in DRAFT ≥4h in future
        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="E2E Publish",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status=Event.Status.DRAFT,
        )

    def _trigger(self, event_type: str, overrides: list[str]) -> subprocess.CompletedProcess:
        cli = _cli_path()
        assert cli, "STRIPE_CLI_BIN not set or not found"
        cmd = [cli, "trigger", event_type]
        for ov in overrides:
            cmd.extend(["--override", ov])
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    def test_pay_and_publish_e2e(self, mock_stripe_create):
        """Organizer pays to publish event → webhook publishes event."""
        from bookings.models import Booking
        from events.models import Event

        # Mock Stripe session creation for the pay-and-publish endpoint
        fake_session = MagicMock()
        fake_session.url = "https://checkout.stripe.com/pay/cs_cli_event_123"
        fake_session.id = "cs_cli_event_123"
        mock_stripe_create.return_value = fake_session

        # Call endpoint to create organizer booking + checkout session
        url = reverse('event-pay-and-publish', args=[self.event.id])
        res = self.client.post(url, {"lang": "fr"}, format='json')
        self.assertEqual(res.status_code, 200, msg=res.data)
        self.assertIn("url", res.data)
        self.assertIn("session_id", res.data)
        self.assertIn("booking_id", res.data)

        session_id = res.data["session_id"]
        booking_id = res.data["booking_id"]

        # Trigger webhook via Stripe CLI (checkout.session.completed)
        trig = self._trigger(
            "checkout.session.completed",
            [
                f"checkout_session:id={session_id}",
                f"checkout_session:payment_intent=pi_cli_event_456",
                f"checkout_session:client_reference_id={booking_id}",
                f"checkout_session:metadata[booking_public_id]={booking_id}",
            ],
        )
        self.assertEqual(trig.returncode, 0, msg=trig.stderr)

        # Poll until booking confirmed and event published (max ~10s)
        deadline = time.time() + 10
        while time.time() < deadline:
            # Reload models
            b = Booking.objects.get(public_id=booking_id)
            e = Event.objects.get(id=self.event.id)
            if b.status == Booking.BookingStatus.CONFIRMED and e.status == Event.Status.PUBLISHED:
                break
            time.sleep(0.5)

        # Assertions
        b = Booking.objects.get(public_id=booking_id)
        e = Event.objects.get(id=self.event.id)
        self.assertEqual(b.status, Booking.BookingStatus.CONFIRMED)
        self.assertEqual(e.status, Event.Status.PUBLISHED)

