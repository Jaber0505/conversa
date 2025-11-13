"""
Tests for Event API views.

These tests ensure that EventViewSet correctly uses different serializers
for list and detail views, and that API endpoints work as expected.
"""

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from languages.models import Language
from partners.models import Partner
from events.models import Event
from events.serializers import EventSerializer, EventDetailSerializer
from events.views import EventViewSet
from bookings.models import Booking

User = get_user_model()


class EventViewSetSerializerClassTestCase(TestCase):
    """Test that EventViewSet uses correct serializers for different actions."""

    def setUp(self):
        """Create test fixtures."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            age=25,
            consent_given=True,
        )

        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

        self.partner = Partner.objects.create(
            name="Test Venue",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Create event
        start_time = timezone.now() + timedelta(days=2)
        start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty=Event.Difficulty.MEDIUM,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_get_serializer_class_for_list(self):
        """ViewSet should use EventSerializer for list action."""
        viewset = EventViewSet()
        viewset.action = 'list'

        serializer_class = viewset.get_serializer_class()

        self.assertEqual(serializer_class, EventSerializer)

    def test_get_serializer_class_for_retrieve(self):
        """ViewSet should use EventDetailSerializer for retrieve action."""
        viewset = EventViewSet()
        viewset.action = 'retrieve'

        serializer_class = viewset.get_serializer_class()

        self.assertEqual(serializer_class, EventDetailSerializer)

    def test_get_serializer_class_for_create(self):
        """ViewSet should use EventSerializer for create action."""
        viewset = EventViewSet()
        viewset.action = 'create'

        serializer_class = viewset.get_serializer_class()

        self.assertEqual(serializer_class, EventSerializer)

    def test_get_serializer_class_for_update(self):
        """ViewSet should use EventSerializer for update action."""
        viewset = EventViewSet()
        viewset.action = 'update'

        serializer_class = viewset.get_serializer_class()

        self.assertEqual(serializer_class, EventSerializer)


class EventAPIListTestCase(TestCase):
    """Test Event list API endpoint."""

    def setUp(self):
        """Create test fixtures."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )

        self.language = Language.objects.create(
            code="en",
            label_fr="Anglais",
            label_en="English",
            label_nl="Engels",
            is_active=True,
        )

        self.partner = Partner.objects.create(
            name="Test Bar",
            address="456 Test Ave",
            city="Brussels",
            capacity=30,
            is_active=True,
        )

        # Create event
        start_time = timezone.now() + timedelta(days=3)
        start_time = start_time.replace(hour=18, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="English Conversation",
            difficulty=Event.Difficulty.EASY,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_list_endpoint_does_not_include_detail_fields(self):
        """List endpoint should NOT include expensive detail fields."""
        response = self.client.get('/api/v1/events/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

        event_data = response.data['results'][0]

        # Should have basic fields
        self.assertIn('id', event_data)
        self.assertIn('theme', event_data)
        self.assertIn('partner_name', event_data)
        self.assertIn('partner_address', event_data)

        # Should NOT have detail-only fields (performance optimization)
        self.assertNotIn('participants_count', event_data)
        self.assertNotIn('available_slots', event_data)
        self.assertNotIn('is_full', event_data)
        self.assertNotIn('language_name', event_data)
        self.assertNotIn('organizer_first_name', event_data)


class EventAPIDetailTestCase(TestCase):
    """Test Event detail API endpoint."""

    def setUp(self):
        """Create test fixtures."""
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            email="organizer@example.com",
            password="testpass123",
            first_name="Alice",
            last_name="Smith",
            age=30,
            consent_given=True,
        )

        # Create participant
        self.participant = User.objects.create_user(
            email="participant@example.com",
            password="testpass123",
            first_name="Bob",
            last_name="Jones",
            age=28,
            consent_given=True,
        )

        self.language = Language.objects.create(
            code="es",
            label_fr="Espagnol",
            label_en="Spanish",
            label_nl="Spaans",
            is_active=True,
        )

        self.partner = Partner.objects.create(
            name="Spanish Café",
            address="789 Plaza Mayor",
            city="Brussels",
            capacity=20,
            is_active=True,
        )

        # Create event
        start_time = timezone.now() + timedelta(days=5)
        start_time = start_time.replace(hour=20, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.organizer,
            partner=self.partner,
            language=self.language,
            theme="Spanish Tapas & Talk",
            difficulty=Event.Difficulty.HARD,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

        # Create confirmed booking
        booking = Booking.objects.create(
            user=self.participant,
            event=self.event,
            amount_cents=self.event.price_cents,
            currency="EUR",
        )
        booking.mark_confirmed(payment_intent_id="pi_test_123")

        # Authenticate
        self.client.force_authenticate(user=self.organizer)

    def test_detail_endpoint_includes_all_fields(self):
        """Detail endpoint should include ALL fields including computed ones."""
        response = self.client.get(f'/api/v1/events/{self.event.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        event_data = response.data

        # Should have basic fields
        self.assertEqual(event_data['id'], self.event.id)
        self.assertEqual(event_data['theme'], "Spanish Tapas & Talk")
        self.assertEqual(event_data['difficulty'], "hard")

        # Should have detail fields
        self.assertEqual(event_data['partner_address'], "789 Plaza Mayor")
        self.assertEqual(event_data['partner_capacity'], 20)
        self.assertEqual(event_data['language_name'], "Spanish")
        self.assertEqual(event_data['organizer_first_name'], "Alice")
        self.assertEqual(event_data['organizer_last_name'], "Smith")

        # Should have computed fields
        self.assertEqual(event_data['participants_count'], 1)  # 1 confirmed booking
        self.assertEqual(event_data['available_slots'], 19)    # 20 - 1 = 19
        self.assertFalse(event_data['is_full'])                # Not full yet

    def test_detail_endpoint_participants_count_accuracy(self):
        """Detail endpoint should accurately count only CONFIRMED participants."""
        # Add another confirmed participant
        participant2 = User.objects.create_user(
            email="participant2@example.com",
            password="testpass123",
            age=26,
            consent_given=True,
        )
        booking2 = Booking.objects.create(
            user=participant2,
            event=self.event,
            amount_cents=self.event.price_cents,
            currency="EUR",
        )
        booking2.mark_confirmed(payment_intent_id="pi_test_456")

        # Add a PENDING booking (should not be counted)
        participant3 = User.objects.create_user(
            email="participant3@example.com",
            password="testpass123",
            age=24,
            consent_given=True,
        )
        Booking.objects.create(
            user=participant3,
            event=self.event,
            amount_cents=self.event.price_cents,
            currency="EUR",
            # Still PENDING
        )

        response = self.client.get(f'/api/v1/events/{self.event.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should count only 2 confirmed participants (not 3)
        self.assertEqual(response.data['participants_count'], 2)
        self.assertEqual(response.data['available_slots'], 18)  # 20 - 2 = 18

    def test_detail_endpoint_is_full_when_capacity_reached(self):
        """Detail endpoint should correctly report is_full when capacity is reached."""
        # Fill remaining capacity (already have 1, need 19 more for total of 20)
        for i in range(19):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="testpass123",
                age=25,
                consent_given=True,
            )
            booking = Booking.objects.create(
                user=user,
                event=self.event,
                amount_cents=self.event.price_cents,
                currency="EUR",
            )
            booking.mark_confirmed(payment_intent_id=f"pi_test_{i}")

        response = self.client.get(f'/api/v1/events/{self.event.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should now be full
        self.assertEqual(response.data['participants_count'], 20)
        self.assertEqual(response.data['available_slots'], 0)
        self.assertTrue(response.data['is_full'])

    def test_detail_endpoint_requires_authentication(self):
        """Detail endpoint should require authentication."""
        self.client.force_authenticate(user=None)  # Unauthenticate

        response = self.client.get(f'/api/v1/events/{self.event.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
