"""
Tests for Event serializers.

These tests ensure that EventSerializer and EventDetailSerializer
correctly serialize event data with all computed fields.
"""

from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from events.serializers import EventSerializer, EventDetailSerializer
from bookings.models import Booking, BookingStatus

User = get_user_model()


class EventSerializerTestCase(TestCase):
    """Test suite for EventSerializer (list view)."""

    def setUp(self):
        """Create test fixtures."""
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            email="organizer@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
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
            address="123 Test Street",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Create event 2 days from now at 14:00
        start_time = timezone.now() + timedelta(days=2)
        start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="French Conversation",
            difficulty=Event.Difficulty.MEDIUM,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

    def test_event_serializer_basic_fields(self):
        """EventSerializer should include basic fields."""
        request = self.factory.get('/api/v1/events/')
        request.user = self.user

        serializer = EventSerializer(self.event, context={'request': request})
        data = serializer.data

        # Check basic fields
        self.assertEqual(data['id'], self.event.id)
        self.assertEqual(data['organizer_id'], self.user.id)
        self.assertEqual(data['partner_name'], "Test Venue")
        self.assertEqual(data['partner_city'], "Brussels")
        self.assertEqual(data['partner_address'], "123 Test Street")
        self.assertEqual(data['language_code'], "fr")
        self.assertEqual(data['theme'], "French Conversation")
        self.assertEqual(data['difficulty'], "medium")
        self.assertEqual(data['price_cents'], self.event.price_cents)
        self.assertEqual(data['status'], "PUBLISHED")

    def test_event_serializer_does_not_include_detail_fields(self):
        """EventSerializer should NOT include detail-only fields."""
        request = self.factory.get('/api/v1/events/')
        request.user = self.user

        serializer = EventSerializer(self.event, context={'request': request})
        data = serializer.data

        # These fields should NOT be in the basic serializer
        self.assertNotIn('participants_count', data)
        self.assertNotIn('available_slots', data)
        self.assertNotIn('is_full', data)
        self.assertNotIn('partner_capacity', data)
        self.assertNotIn('language_name', data)
        self.assertNotIn('organizer_first_name', data)
        self.assertNotIn('organizer_last_name', data)


class EventDetailSerializerTestCase(TestCase):
    """Test suite for EventDetailSerializer (detail view)."""

    def setUp(self):
        """Create test fixtures."""
        self.factory = RequestFactory()

        self.organizer = User.objects.create_user(
            email="organizer@example.com",
            password="testpass123",
            first_name="Marie",
            last_name="Dubois",
            age=30,
            consent_given=True,
        )

        # Create participants
        self.participant1 = User.objects.create_user(
            email="participant1@example.com",
            password="testpass123",
            first_name="Sophie",
            last_name="Martin",
            age=25,
            consent_given=True,
        )

        self.participant2 = User.objects.create_user(
            email="participant2@example.com",
            password="testpass123",
            first_name="Thomas",
            last_name="Bernard",
            age=28,
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
            name="Café Polyglotte",
            address="42 Rue du Marché",
            city="Brussels",
            capacity=30,
            is_active=True,
        )

        # Create event 3 days from now at 18:00
        start_time = timezone.now() + timedelta(days=3)
        start_time = start_time.replace(hour=18, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.organizer,
            partner=self.partner,
            language=self.language,
            theme="English Practice Session",
            difficulty=Event.Difficulty.EASY,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

        # Create confirmed bookings for participants
        for user in [self.participant1, self.participant2]:
            booking = Booking.objects.create(
                user=user,
                event=self.event,
                amount_cents=self.event.price_cents,
                currency="EUR",
            )
            booking.mark_confirmed(payment_intent_id=f"pi_test_{user.id}")

    def test_detail_serializer_includes_all_fields(self):
        """EventDetailSerializer should include all fields including computed ones."""
        request = self.factory.get(f'/api/v1/events/{self.event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(self.event, context={'request': request})
        data = serializer.data

        # Check basic fields (inherited from EventSerializer)
        self.assertEqual(data['id'], self.event.id)
        self.assertEqual(data['theme'], "English Practice Session")

        # Check additional partner fields
        self.assertEqual(data['partner_address'], "42 Rue du Marché")
        self.assertEqual(data['partner_capacity'], 30)

        # Check additional language fields
        self.assertEqual(data['language_name'], "English")

        # Check organizer fields
        self.assertEqual(data['organizer_first_name'], "Marie")
        self.assertEqual(data['organizer_last_name'], "Dubois")

    def test_detail_serializer_participants_count(self):
        """EventDetailSerializer should correctly count confirmed participants."""
        request = self.factory.get(f'/api/v1/events/{self.event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(self.event, context={'request': request})
        data = serializer.data

        # Should have 2 confirmed participants
        self.assertEqual(data['participants_count'], 2)

    def test_detail_serializer_available_slots(self):
        """EventDetailSerializer should correctly calculate available slots."""
        request = self.factory.get(f'/api/v1/events/{self.event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(self.event, context={'request': request})
        data = serializer.data

        # Partner capacity is 30, 2 confirmed bookings = 28 available
        self.assertEqual(data['available_slots'], 28)

    def test_detail_serializer_is_full_false(self):
        """EventDetailSerializer should correctly report is_full as False when slots available."""
        request = self.factory.get(f'/api/v1/events/{self.event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(self.event, context={'request': request})
        data = serializer.data

        # Event is not full (2/30)
        self.assertFalse(data['is_full'])

    def test_detail_serializer_is_full_true(self):
        """EventDetailSerializer should correctly report is_full as True when capacity reached."""
        # Create a small capacity partner
        small_partner = Partner.objects.create(
            name="Small Café",
            address="1 Tiny Street",
            city="Brussels",
            capacity=3,  # Only 3 seats
            is_active=True,
        )

        # Create event at small partner
        start_time = timezone.now() + timedelta(days=4)
        start_time = start_time.replace(hour=19, minute=0, second=0, microsecond=0)

        small_event = Event.objects.create(
            organizer=self.organizer,
            partner=small_partner,
            language=self.language,
            theme="Small Group",
            difficulty=Event.Difficulty.EASY,
            datetime_start=start_time,
            status=Event.Status.PUBLISHED,
        )

        # Fill up the capacity with 3 confirmed bookings
        for i in range(3):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="testpass123",
                age=25,
                consent_given=True,
            )
            booking = Booking.objects.create(
                user=user,
                event=small_event,
                amount_cents=small_event.price_cents,
                currency="EUR",
            )
            booking.mark_confirmed(payment_intent_id=f"pi_test_{i}")

        # Now serialize
        request = self.factory.get(f'/api/v1/events/{small_event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(small_event, context={'request': request})
        data = serializer.data

        # Event should be full (3/3)
        self.assertEqual(data['participants_count'], 3)
        self.assertEqual(data['available_slots'], 0)
        self.assertTrue(data['is_full'])

    def test_detail_serializer_only_counts_confirmed_bookings(self):
        """EventDetailSerializer should only count CONFIRMED bookings, not PENDING or CANCELLED."""
        # Create a PENDING booking
        pending_user = User.objects.create_user(
            email="pending@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        Booking.objects.create(
            user=pending_user,
            event=self.event,
            amount_cents=self.event.price_cents,
            currency="EUR",
            status=BookingStatus.PENDING,  # Still pending
        )

        # Create a CANCELLED booking
        cancelled_user = User.objects.create_user(
            email="cancelled@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        cancelled_booking = Booking.objects.create(
            user=cancelled_user,
            event=self.event,
            amount_cents=self.event.price_cents,
            currency="EUR",
        )
        cancelled_booking.mark_confirmed(payment_intent_id="pi_test_cancelled")
        cancelled_booking.mark_cancelled()  # Then cancelled

        # Serialize
        request = self.factory.get(f'/api/v1/events/{self.event.id}/')
        request.user = self.organizer

        serializer = EventDetailSerializer(self.event, context={'request': request})
        data = serializer.data

        # Should still only have 2 confirmed participants (not 4)
        self.assertEqual(data['participants_count'], 2)
