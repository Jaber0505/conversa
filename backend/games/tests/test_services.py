"""
Tests for game services.
"""

import pytest
from rest_framework.exceptions import ValidationError, PermissionDenied

from games.models import Game, GameVote, GameStatus
from games.services import GameService


@pytest.mark.django_db
class TestGameServiceCreate:
    """Test suite for GameService.create_game()."""

    def test_create_game_as_organizer_success(self, published_event, organizer_user, organizer_booking):
        """Test organizer can create a game for their published event."""
        # Act
        game = GameService.create_game(
            event=published_event,
            created_by=organizer_user,
            game_type="picture_description",
            difficulty="easy"
        )

        # Assert
        assert game.event == published_event
        assert game.created_by == organizer_user
        assert game.game_type == "picture_description"
        assert game.difficulty == published_event.difficulty
        assert game.status == GameStatus.ACTIVE
        assert game.question_text is not None
        assert game.correct_answer is not None
        assert game.language_code == "en"

    def test_create_game_non_organizer_fails(self, published_event, participant_user, organizer_booking):
        """Test non-organizer cannot create a game."""
        # Act & Assert
        with pytest.raises(PermissionDenied) as exc:
            GameService.create_game(
                event=published_event,
                created_by=participant_user,
                game_type="picture_description",
                difficulty="easy"
            )
        assert "only the event organizer" in str(exc.value).lower()

    def test_create_game_for_draft_event_fails(self, draft_event, organizer_user):
        """Test cannot create game for non-published event."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            GameService.create_game(
                event=draft_event,
                created_by=organizer_user,
                game_type="picture_description",
                difficulty="easy"
            )
        assert "published" in str(exc.value).lower()

    def test_create_game_for_future_event_fails(self, future_event, organizer_user):
        """Test cannot create game for event that hasn't started."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            GameService.create_game(
                event=future_event,
                created_by=organizer_user,
                game_type="picture_description",
                difficulty="easy"
            )
        assert "started" in str(exc.value).lower()

    def test_create_game_for_finished_event_fails(self, finished_event, organizer_user):
        """Test cannot create game for finished event."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            GameService.create_game(
                event=finished_event,
                created_by=organizer_user,
                game_type="picture_description",
                difficulty="easy"
            )
        # Event status is FINISHED, not PUBLISHED, so error mentions "published"
        assert "published" in str(exc.value).lower() or "ended" in str(exc.value).lower()

    def test_create_game_when_active_game_exists_fails(self, published_event, organizer_user, active_game, organizer_booking):
        """Test cannot create game when another game is active."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            GameService.create_game(
                event=published_event,
                created_by=organizer_user,
                game_type="word_association",
                difficulty="medium"
            )
        assert "already has an active game" in str(exc.value).lower()

    def test_create_game_staff_user_success(self, published_event, staff_user, organizer_booking):
        """Test staff user can create game even if not organizer."""
        # Act
        game = GameService.create_game(
            event=published_event,
            created_by=staff_user,
            game_type="picture_description",
            difficulty="easy"
        )

        # Assert
        assert game is not None
        assert game.created_by == staff_user


@pytest.mark.django_db
class TestGameServiceVoting:
    """Test suite for GameService.submit_vote()."""

    def test_submit_vote_as_participant_success(self, active_game, participant_user, confirmed_booking):
        """Test confirmed participant can vote."""
        # Act
        vote, game_completed = GameService.submit_vote(
            game=active_game,
            user=participant_user,
            answer="mountain"
        )

        # Assert
        assert vote.game == active_game
        assert vote.user == participant_user
        assert vote.answer == "mountain"
        assert isinstance(game_completed, bool)

    def test_submit_vote_duplicate_fails(self, active_game, participant_user, confirmed_booking):
        """Test cannot vote twice on same game."""
        # Arrange
        GameService.submit_vote(active_game, participant_user, "mountain")

        # Act & Assert - Database constraint will prevent duplicate
        from django.db import IntegrityError
        with pytest.raises((ValidationError, IntegrityError)):
            GameService.submit_vote(active_game, participant_user, "beach")

    def test_submit_vote_non_participant_fails(self, active_game, random_user):
        """Test non-participant cannot vote."""
        # Act & Assert
        with pytest.raises(PermissionDenied) as exc:
            GameService.submit_vote(active_game, random_user, "mountain")
        assert "confirmed participants" in str(exc.value).lower()

    def test_submit_vote_pending_booking_fails(self, active_game, participant_user, published_event):
        """Test user with pending booking cannot vote."""
        # Arrange - Create pending booking
        from bookings.models import Booking, BookingStatus
        Booking.objects.create(
            event=published_event,
            user=participant_user,
            amount_cents=700,
            status=BookingStatus.PENDING
        )

        # Act & Assert
        with pytest.raises(PermissionDenied):
            GameService.submit_vote(active_game, participant_user, "mountain")

    def test_submit_vote_on_completed_game_fails(self, completed_game, participant_user, confirmed_booking):
        """Test cannot vote on completed game."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            GameService.submit_vote(completed_game, participant_user, "mountain")
        assert "no longer active" in str(exc.value).lower()

    def test_game_completes_when_all_participants_vote(self, active_game, multiple_participants):
        """Test game completes when all participants vote."""
        # Arrange - 5 participants (from fixture)
        participants = multiple_participants[:3]  # Use 3 participants

        # Act - All vote for same answer
        game_completed = False
        for i, participant in enumerate(participants):
            vote, completed = GameService.submit_vote(active_game, participant, "mountain")
            if i == len(participants) - 1:  # Last vote
                game_completed = completed

        # Assert
        assert game_completed is True
        active_game.refresh_from_db()
        assert active_game.status == GameStatus.COMPLETED
        assert active_game.final_answer == "mountain"
        assert active_game.is_correct == (active_game.correct_answer == "mountain")
        assert active_game.completed_at is not None

    def test_game_completes_on_majority_vote(self, active_game, multiple_participants):
        """Test game completes when majority (>50%) votes for same answer."""
        # Arrange - 5 participants, need 3 votes for majority
        participants = multiple_participants[:5]

        # Act - 3 vote for mountain, triggering completion
        game_completed = False
        for i, participant in enumerate(participants[:3]):
            vote, completed = GameService.submit_vote(active_game, participant, "mountain")
            if i == 2:  # After 3rd vote (majority)
                game_completed = completed

        # Assert
        assert game_completed is True
        active_game.refresh_from_db()
        assert active_game.status == GameStatus.COMPLETED
        assert active_game.final_answer == "mountain"

    def test_game_does_not_complete_without_majority(self, active_game, multiple_participants):
        """Test game does not complete without majority."""
        # Arrange - 5 participants, 2 votes not enough for majority
        participants = multiple_participants[:5]

        # Act - 2 different votes (no majority)
        vote1, completed1 = GameService.submit_vote(active_game, participants[0], "mountain")
        vote2, completed2 = GameService.submit_vote(active_game, participants[1], "beach")

        # Assert
        assert completed1 is False
        assert completed2 is False
        active_game.refresh_from_db()
        assert active_game.status == GameStatus.ACTIVE



@pytest.mark.django_db
class TestGameServiceStats:
    """Test suite for game statistics."""

    def test_get_game_stats_no_votes(self, active_game, organizer_booking):
        """Test stats for game with no votes."""
        # Act
        stats = GameService.get_game_stats(active_game)

        # Assert
        assert stats["total_votes"] == 0
        assert stats["confirmed_participants"] == 1  # Only organizer
        assert stats["vote_counts"] == {}
        assert stats["votes_remaining"] == 1

    def test_get_game_stats_with_votes(self, active_game_with_votes, organizer_booking):
        """Test stats for game with votes."""
        # Act
        stats = GameService.get_game_stats(active_game_with_votes)

        # Assert
        assert stats["total_votes"] == 2
        assert stats["confirmed_participants"] == 3  # Organizer + 2 participants
        assert stats["vote_counts"]["mountain"] == 1
        assert stats["vote_counts"]["beach"] == 1
        assert stats["votes_remaining"] == 1

    def test_get_game_stats_completed_game(self, completed_game, organizer_booking):
        """Test stats for completed game."""
        # Act
        stats = GameService.get_game_stats(completed_game)

        # Assert
        assert stats["total_votes"] == 0  # No votes in fixture


@pytest.mark.django_db
class TestGameServiceGetActiveGame:
    """Test suite for get_active_game."""

    def test_get_active_game_exists(self, active_game):
        """Test getting active game when one exists."""
        # Act
        result = GameService.get_active_game(active_game.event)

        # Assert
        assert result is not None
        assert result.id == active_game.id
        assert result.status == GameStatus.ACTIVE

    def test_get_active_game_none_exists(self, published_event):
        """Test getting active game when none exists."""
        # Act
        result = GameService.get_active_game(published_event)

        # Assert
        assert result is None

    def test_get_active_game_only_completed_exists(self, completed_game):
        """Test getting active game when only completed games exist."""
        # Act
        result = GameService.get_active_game(completed_game.event)

        # Assert
        assert result is None
