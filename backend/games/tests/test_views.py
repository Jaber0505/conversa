"""
Tests for game API views.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from games.models import Game, GameVote, GameStatus


@pytest.mark.django_db
class TestGameListView:
    """Test suite for game list endpoint."""

    def test_list_games_authenticated(self, authenticated_client, active_game, confirmed_booking):
        """Test authenticated user can list games for their events."""
        # Act
        url = reverse('game-list')
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_games_unauthenticated(self, api_client):
        """Test unauthenticated user cannot list games."""
        # Act
        url = reverse('game-list')
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_games_filter_by_event(self, authenticated_client, active_game, confirmed_booking):
        """Test filtering games by event ID."""
        # Act
        url = reverse('game-list')
        response = authenticated_client.get(url, {'event_id': active_game.event.id})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated or a list
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert all(game['event_id'] == active_game.event.id for game in results)

    def test_list_games_filter_by_status(self, authenticated_client, active_game, confirmed_booking):
        """Test filtering games by status."""
        # Act
        url = reverse('game-list')
        response = authenticated_client.get(url, {'status': 'ACTIVE'})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated or a list
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        if len(results) > 0:
            assert all(game['status'] == 'ACTIVE' for game in results)

    def test_list_games_only_accessible_events(self, authenticated_client, participant_user, active_game, confirmed_booking, random_user, published_event, language, partner):
        """Test user only sees games from events they have access to."""
        # Arrange - Create another event with game that user shouldn't see
        from events.models import Event
        other_event = Event.objects.create(
            organizer=random_user,
            partner=partner,
            language=language,
            theme="Other Event",
            difficulty="medium",
            datetime_start=published_event.datetime_start,
            status=Event.Status.PUBLISHED
        )
        other_game = Game.objects.create(
            event=other_event,
            created_by=random_user,
            game_type="picture_description",
            difficulty="easy",
            language_code="en",
            question_id="other_01",
            question_text="Other question",
            correct_answer="other"
        )

        # Act
        url = reverse('game-list')
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated or a list
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        game_ids = [game['id'] for game in results]
        assert active_game.id in game_ids
        assert other_game.id not in game_ids  # Should not see other event's game


@pytest.mark.django_db
class TestGameDetailView:
    """Test suite for game detail endpoint."""

    def test_retrieve_game_details(self, authenticated_client, active_game, confirmed_booking):
        """Test retrieving game details."""
        # Act
        url = reverse('game-detail', kwargs={'pk': active_game.pk})
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == active_game.id
        assert response.data['question_text'] == active_game.question_text
        assert 'stats' in response.data
        assert 'votes' in response.data

    def test_retrieve_game_unauthorized_event(self, authenticated_client, random_user, language, partner, published_event):
        """Test cannot retrieve game from event user doesn't have access to."""
        # Arrange - Create game for event user isn't part of
        from events.models import Event
        from django.utils import timezone
        from datetime import timedelta

        other_event = Event.objects.create(
            organizer=random_user,
            partner=partner,
            language=language,
            theme="Other Event",
            difficulty="medium",
            datetime_start=timezone.now() - timedelta(minutes=10),
            status=Event.Status.PUBLISHED
        )
        other_game = Game.objects.create(
            event=other_event,
            created_by=random_user,
            game_type="picture_description",
            difficulty="easy",
            language_code="en",
            question_id="other_01",
            question_text="Other question",
            correct_answer="other"
        )

        # Act
        url = reverse('game-detail', kwargs={'pk': other_game.pk})
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestGameCreateView:
    """Test suite for game creation endpoint."""

    def test_create_game_as_organizer(self, organizer_client, published_event, organizer_booking):
        """Test organizer can create a game."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'event_id': published_event.id,
            'game_type': 'picture_description'
        }

        # Act
        response = organizer_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['game_type'] == 'picture_description'
        assert response.data['difficulty'] == published_event.difficulty
        assert response.data['status'] == 'ACTIVE'
        assert Game.objects.filter(event=published_event).exists()

    def test_create_game_as_participant_fails(self, authenticated_client, published_event, confirmed_booking):
        """Test participant cannot create a game."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'event_id': published_event.id,
            'game_type': 'picture_description'
        }

        # Act
        response = authenticated_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_game_unauthenticated_fails(self, api_client, published_event):
        """Test unauthenticated user cannot create a game."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'event_id': published_event.id,
            'game_type': 'picture_description'
        }

        # Act
        response = api_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_game_missing_event_id(self, organizer_client):
        """Test creating game without event_id fails."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'game_type': 'picture_description'
        }

        # Act
        response = organizer_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'event_id' in str(response.data).lower()

    def test_create_game_invalid_event_id(self, organizer_client):
        """Test creating game with invalid event_id fails."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'event_id': 99999,
            'game_type': 'picture_description'
        }

        # Act
        response = organizer_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_game_when_active_exists_fails(self, organizer_client, active_game, organizer_booking):
        """Test cannot create game when another is active."""
        # Arrange
        url = reverse('game-create-game')
        data = {
            'event_id': active_game.event.id,
            'game_type': 'word_association'
        }

        # Act
        response = organizer_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGameVoteView:
    """Test suite for vote submission endpoint."""

    def test_submit_vote_as_participant(self, authenticated_client, active_game, confirmed_booking):
        """Test participant can submit a vote."""
        # Arrange
        url = reverse('game-vote', kwargs={'pk': active_game.pk})
        data = {'answer': 'mountain'}

        # Act
        response = authenticated_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert GameVote.objects.filter(
            game=active_game,
            user=confirmed_booking.user,
            answer='mountain'
        ).exists()

    def test_submit_vote_duplicate_fails(self, authenticated_client, active_game, confirmed_booking):
        """Test cannot vote twice."""
        # Arrange
        url = reverse('game-vote', kwargs={'pk': active_game.pk})
        authenticated_client.post(url, {'answer': 'mountain'}, format='json')

        # Act - Try to vote again
        response = authenticated_client.post(url, {'answer': 'beach'}, format='json')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_vote_as_non_participant_fails(self, api_client, active_game, random_user):
        """Test non-participant cannot vote."""
        # Arrange
        api_client.force_authenticate(user=random_user)
        url = reverse('game-vote', kwargs={'pk': active_game.pk})
        data = {'answer': 'mountain'}

        # Act
        response = api_client.post(url, data, format='json')

        # Assert
        # 404 because queryset filters games user has no access to, or 403 if game found
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_submit_vote_unauthenticated_fails(self, api_client, active_game):
        """Test unauthenticated user cannot vote."""
        # Arrange
        url = reverse('game-vote', kwargs={'pk': active_game.pk})
        data = {'answer': 'mountain'}

        # Act
        response = api_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_vote_empty_answer_fails(self, authenticated_client, active_game, confirmed_booking):
        """Test voting with empty answer fails."""
        # Arrange
        url = reverse('game-vote', kwargs={'pk': active_game.pk})
        data = {'answer': ''}

        # Act
        response = authenticated_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_vote_completes_game(self, authenticated_client, active_game, multiple_participants):
        """Test game completes when all participants vote."""
        # Arrange - Get 3 participants
        from rest_framework.test import APIClient
        participants = multiple_participants[:3]
        url = reverse('game-vote', kwargs={'pk': active_game.pk})

        # Act - All vote
        for participant in participants:
            client = APIClient()
            client.force_authenticate(user=participant)
            response = client.post(url, {'answer': 'mountain'}, format='json')

        # Assert - Game should be completed after last vote
        active_game.refresh_from_db()
        assert active_game.status == GameStatus.COMPLETED
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestGameStatsView:
    """Test suite for game stats endpoint."""

    def test_get_game_stats(self, authenticated_client, active_game, confirmed_booking):
        """Test retrieving game statistics."""
        # Arrange
        url = reverse('game-stats', kwargs={'pk': active_game.pk})

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'total_votes' in response.data
        assert 'confirmed_participants' in response.data
        assert 'vote_counts' in response.data
        assert 'votes_remaining' in response.data
        assert 'time_remaining_seconds' in response.data

    def test_get_stats_with_votes(self, authenticated_client, active_game_with_votes, confirmed_booking, organizer_booking):
        """Test stats include vote counts."""
        # Arrange
        url = reverse('game-stats', kwargs={'pk': active_game_with_votes.pk})

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_votes'] == 2
        assert 'mountain' in response.data['vote_counts']
        assert 'beach' in response.data['vote_counts']


@pytest.mark.django_db
class TestActiveGameView:
    """Test suite for active game endpoint."""

    def test_get_active_game(self, authenticated_client, active_game, confirmed_booking):
        """Test retrieving active game for an event."""
        # Arrange
        url = reverse('game-active-game')

        # Act
        response = authenticated_client.get(url, {'event_id': active_game.event.id})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == active_game.id
        assert response.data['status'] == 'ACTIVE'

    def test_get_active_game_missing_event_id(self, authenticated_client):
        """Test getting active game without event_id fails."""
        # Arrange
        url = reverse('game-active-game')

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_active_game_none_exists(self, authenticated_client, published_event, confirmed_booking):
        """Test getting active game when none exists returns 404."""
        # Arrange
        url = reverse('game-active-game')

        # Act
        response = authenticated_client.get(url, {'event_id': published_event.id})

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_active_game_unauthorized_event(self, authenticated_client, random_user, language, partner):
        """Test cannot get active game for event user doesn't have access to."""
        # Arrange - Create game for event user isn't part of
        from events.models import Event
        from django.utils import timezone
        from datetime import timedelta

        other_event = Event.objects.create(
            organizer=random_user,
            partner=partner,
            language=language,
            theme="Other Event",
            difficulty="medium",
            datetime_start=timezone.now() - timedelta(minutes=10),
            status=Event.Status.PUBLISHED
        )
        other_game = Game.objects.create(
            event=other_event,
            created_by=random_user,
            game_type="picture_description",
            difficulty="easy",
            language_code="en",
            question_id="other_01",
            question_text="Other question",
            correct_answer="other"
        )

        url = reverse('game-active-game')

        # Act
        response = authenticated_client.get(url, {'event_id': other_event.id})

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
