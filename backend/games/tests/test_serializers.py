"""
Tests for game serializers.
"""

import pytest

from games.serializers import (
    GameSerializer,
    GameCreateSerializer,
    VoteSubmitSerializer,
    GameStatsSerializer,
    GameVoteSerializer,
)
from games.models import GameVote


@pytest.mark.django_db
class TestGameSerializer:
    """Test suite for GameSerializer."""

    def test_serialize_active_game(self, active_game, api_client, participant_user):
        """Test serializing an active game."""
        # Arrange
        request = api_client.get('/').wsgi_request
        request.user = participant_user

        # Act
        serializer = GameSerializer(active_game, context={'request': request})
        data = serializer.data

        # Assert
        assert data['id'] == active_game.id
        assert data['public_id'] == str(active_game.public_id)
        assert data['game_type'] == 'picture_description'
        assert data['difficulty'] == 'easy'
        assert data['status'] == 'ACTIVE'
        assert data['question_text'] == active_game.question_text
        assert data['image_url'] == active_game.image_url
        assert 'correct_answer' not in data or data.get('correct_answer') is None  # Should not expose correct answer
        assert '_links' in data
        assert 'self' in data['_links']

    def test_serialize_completed_game(self, completed_game, api_client, participant_user):
        """Test serializing a completed game."""
        # Arrange
        request = api_client.get('/').wsgi_request
        request.user = participant_user

        # Act
        serializer = GameSerializer(completed_game, context={'request': request})
        data = serializer.data

        # Assert
        assert data['status'] == 'COMPLETED'
        assert data['is_correct'] is True
        assert data['final_answer'] == 'city'
        assert data['completed_at'] is not None

    def test_serialize_game_with_stats(self, active_game_with_votes, api_client, participant_user, organizer_booking):
        """Test game serialization includes stats."""
        # Arrange
        request = api_client.get('/').wsgi_request
        request.user = participant_user

        # Act
        serializer = GameSerializer(active_game_with_votes, context={'request': request})
        data = serializer.data

        # Assert
        assert 'stats' in data
        assert data['stats']['total_votes'] == 2
        assert 'vote_counts' in data['stats']

    def test_serialize_game_with_votes(self, active_game_with_votes, api_client, participant_user):
        """Test game serialization includes votes."""
        # Arrange
        request = api_client.get('/').wsgi_request
        request.user = participant_user

        # Act
        serializer = GameSerializer(active_game_with_votes, context={'request': request})
        data = serializer.data

        # Assert
        assert 'votes' in data
        assert len(data['votes']) == 2


@pytest.mark.django_db
class TestGameVoteSerializer:
    """Test suite for GameVoteSerializer."""

    def test_serialize_vote(self, active_game, participant_user, confirmed_booking):
        """Test serializing a vote."""
        # Arrange
        vote = GameVote.objects.create(
            game=active_game,
            user=participant_user,
            answer="mountain"
        )

        # Act
        serializer = GameVoteSerializer(vote)
        data = serializer.data

        # Assert
        assert data['id'] == vote.id
        assert data['user_id'] == participant_user.id
        assert 'user_email' in data  # Field exists
        assert data['answer'] == "mountain"
        assert 'created_at' in data


@pytest.mark.django_db
class TestGameCreateSerializer:
    """Test suite for GameCreateSerializer."""

    def test_valid_game_creation_data(self):
        """Test validation of valid game creation data."""
        # Arrange
        data = {
            'game_type': 'picture_description'
        }

        # Act
        serializer = GameCreateSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        assert serializer.validated_data['game_type'] == 'picture_description'

    def test_invalid_game_type(self):
        """Test validation fails for invalid game type."""
        # Arrange
        data = {
            'game_type': 'invalid_type'
        }

        # Act
        serializer = GameCreateSerializer(data=data)

        # Assert
        assert not serializer.is_valid()
        assert 'game_type' in serializer.errors

    def test_missing_game_type(self):
        """Test validation fails when game type is missing."""
        serializer = GameCreateSerializer(data={})
        assert not serializer.is_valid()
        assert 'game_type' in serializer.errors


@pytest.mark.django_db
class TestVoteSubmitSerializer:
    """Test suite for VoteSubmitSerializer."""

    def test_valid_vote_submission(self):
        """Test validation of valid vote data."""
        # Arrange
        data = {'answer': 'mountain'}

        # Act
        serializer = VoteSubmitSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        assert serializer.validated_data['answer'] == 'mountain'

    def test_empty_answer_fails(self):
        """Test validation fails for empty answer."""
        # Arrange
        data = {'answer': ''}

        # Act
        serializer = VoteSubmitSerializer(data=data)

        # Assert
        assert not serializer.is_valid()
        assert 'answer' in serializer.errors

    def test_whitespace_only_answer_fails(self):
        """Test validation fails for whitespace-only answer."""
        # Arrange
        data = {'answer': '   '}

        # Act
        serializer = VoteSubmitSerializer(data=data)

        # Assert
        assert not serializer.is_valid()
        assert 'answer' in serializer.errors

    def test_answer_trimmed(self):
        """Test answer is trimmed of whitespace."""
        # Arrange
        data = {'answer': '  mountain  '}

        # Act
        serializer = VoteSubmitSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        assert serializer.validated_data['answer'] == 'mountain'


@pytest.mark.django_db
class TestGameStatsSerializer:
    """Test suite for GameStatsSerializer."""

    def test_serialize_stats(self):
        """Test serializing game statistics."""
        # Arrange
        stats_data = {
            'total_votes': 3,
            'confirmed_participants': 5,
            'vote_counts': {'mountain': 2, 'beach': 1},
            'votes_remaining': 2
        }

        # Act
        serializer = GameStatsSerializer(data=stats_data)

        # Assert
        assert serializer.is_valid()
        data = serializer.validated_data
        assert data['total_votes'] == 3
        assert data['confirmed_participants'] == 5
        assert data['vote_counts'] == {'mountain': 2, 'beach': 1}
        assert data['votes_remaining'] == 2
