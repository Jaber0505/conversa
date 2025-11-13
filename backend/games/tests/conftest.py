"""
Pytest fixtures for games tests.
"""

import pytest
from django.utils import timezone
from datetime import timedelta

from users.models import User
from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from games.models import Game, GameStatus


@pytest.fixture
def organizer_user(db):
    """Create organizer user."""
    return User.objects.create_user(
        email="organizer@test.com",
        password="testpass123",
        is_active=True,
        age=25,
        first_name="Organizer",
        last_name="User"
    )


@pytest.fixture
def participant_user(db):
    """Create participant user."""
    return User.objects.create_user(
        email="participant@test.com",
        password="testpass123",
        is_active=True,
        age=25,
        first_name="Participant",
        last_name="User"
    )


@pytest.fixture
def participant_user_2(db):
    """Create second participant user."""
    return User.objects.create_user(
        email="participant2@test.com",
        password="testpass123",
        is_active=True,
        age=25,
        first_name="Participant2",
        last_name="User"
    )


@pytest.fixture
def participant_user_3(db):
    """Create third participant user."""
    return User.objects.create_user(
        email="participant3@test.com",
        password="testpass123",
        is_active=True,
        age=25,
        first_name="Participant3",
        last_name="User"
    )


@pytest.fixture
def random_user(db):
    """Create random user (not participant)."""
    return User.objects.create_user(
        email="random@test.com",
        password="testpass123",
        is_active=True,
        age=25,
        first_name="Random",
        last_name="User"
    )


@pytest.fixture
def staff_user(db):
    """Create staff user."""
    return User.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        is_active=True,
        is_staff=True,
        age=25,
        first_name="Staff",
        last_name="User"
    )


@pytest.fixture
def language(db):
    """Create language."""
    return Language.objects.create(
        code="en",
        label_fr="Anglais",
        label_en="English",
        label_nl="Engels"
    )


@pytest.fixture
def french_language(db):
    """Create French language."""
    return Language.objects.create(
        code="fr",
        label_fr="Français",
        label_en="French",
        label_nl="Frans"
    )


@pytest.fixture
def partner(db):
    """Create partner venue."""
    return Partner.objects.create(
        name="Test Venue",
        address="123 Test St",
        city="Brussels",
        capacity=20,
        is_active=True
    )


@pytest.fixture
def draft_event(db, organizer_user, language, partner):
    """Create a draft event."""
    return Event.objects.create(
        organizer=organizer_user,
        partner=partner,
        language=language,
        theme="Draft Event",
        difficulty="medium",
        datetime_start=timezone.now() + timedelta(hours=4),
        status=Event.Status.DRAFT
    )


@pytest.fixture
def published_event(db, organizer_user, language, partner):
    """Create a published event that has started."""
    event = Event.objects.create(
        organizer=organizer_user,
        partner=partner,
        language=language,
        theme="Published Event",
        difficulty="medium",
        datetime_start=timezone.now() - timedelta(minutes=10),  # Started 10 min ago
        status=Event.Status.PUBLISHED,
        published_at=timezone.now() - timedelta(hours=1)
    )
    return event


@pytest.fixture
def future_event(db, organizer_user, language, partner):
    """Create a published event that hasn't started yet."""
    event = Event.objects.create(
        organizer=organizer_user,
        partner=partner,
        language=language,
        theme="Future Event",
        difficulty="medium",
        datetime_start=timezone.now() + timedelta(hours=2),
        status=Event.Status.PUBLISHED,
        published_at=timezone.now()
    )
    return event


@pytest.fixture
def finished_event(db, organizer_user, language, partner):
    """Create a finished event."""
    event = Event.objects.create(
        organizer=organizer_user,
        partner=partner,
        language=language,
        theme="Finished Event",
        difficulty="medium",
        datetime_start=timezone.now() - timedelta(hours=3),
        status=Event.Status.FINISHED
    )
    return event


@pytest.fixture
def confirmed_booking(db, published_event, participant_user):
    """Create confirmed booking for participant."""
    booking = Booking.objects.create(
        event=published_event,
        user=participant_user,
        amount_cents=700,
        status=BookingStatus.CONFIRMED,
        confirmed_at=timezone.now()
    )
    return booking


@pytest.fixture
def confirmed_booking_2(db, published_event, participant_user_2):
    """Create confirmed booking for second participant."""
    booking = Booking.objects.create(
        event=published_event,
        user=participant_user_2,
        amount_cents=700,
        status=BookingStatus.CONFIRMED,
        confirmed_at=timezone.now()
    )
    return booking


@pytest.fixture
def confirmed_booking_3(db, published_event, participant_user_3):
    """Create confirmed booking for third participant."""
    booking = Booking.objects.create(
        event=published_event,
        user=participant_user_3,
        amount_cents=700,
        status=BookingStatus.CONFIRMED,
        confirmed_at=timezone.now()
    )
    return booking


@pytest.fixture
def organizer_booking(db, published_event, organizer_user):
    """Create confirmed booking for organizer."""
    booking = Booking.objects.create(
        event=published_event,
        user=organizer_user,
        amount_cents=700,
        status=BookingStatus.CONFIRMED,
        confirmed_at=timezone.now(),
        is_organizer_booking=True
    )
    return booking


@pytest.fixture
def active_game(db, published_event, organizer_user):
    """Create an active game."""
    return Game.objects.create(
        event=published_event,
        created_by=organizer_user,
        game_type="picture_description",
        difficulty="easy",
        language_code="en",
        question_id="test_01",
        question_text="What do you see in this picture?",
        correct_answer="mountain",
        image_url="https://example.com/image.jpg",
        status=GameStatus.ACTIVE
    )


@pytest.fixture
def active_game_with_votes(db, active_game, participant_user, participant_user_2, confirmed_booking, confirmed_booking_2):
    """Create an active game with some votes."""
    from games.models import GameVote

    GameVote.objects.create(
        game=active_game,
        user=participant_user,
        answer="mountain"
    )
    GameVote.objects.create(
        game=active_game,
        user=participant_user_2,
        answer="beach"
    )
    return active_game


@pytest.fixture
def completed_game(db, published_event, organizer_user):
    """Create a completed game."""
    return Game.objects.create(
        event=published_event,
        created_by=organizer_user,
        game_type="picture_description",
        difficulty="hard",
        language_code="en",
        question_id="test_03",
        question_text="Describe this image",
        correct_answer="city",
        status=GameStatus.COMPLETED,
        completed_at=timezone.now(),
        is_correct=True,
        final_answer="city"
    )


@pytest.fixture
def multiple_participants(db, published_event, organizer_user):
    """Create multiple confirmed participants for an event."""
    users = []
    for i in range(5):
        user = User.objects.create_user(
            email=f"participant{i}@test.com",
            password="testpass123",
            is_active=True,
            age=25,
            first_name=f"Participant{i}",
            last_name="User"
        )
        Booking.objects.create(
            event=published_event,
            user=user,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        users.append(user)
    return users


@pytest.fixture
def api_client():
    """Create API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, participant_user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=participant_user)
    return api_client


@pytest.fixture
def organizer_client(api_client, organizer_user):
    """Create authenticated API client for organizer."""
    api_client.force_authenticate(user=organizer_user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    """Create authenticated API client for staff."""
    api_client.force_authenticate(user=staff_user)
    return api_client
