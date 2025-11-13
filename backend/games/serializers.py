"""
Game serializers for API responses.
"""

from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Game, GameVote, GameType, GameDifficulty, GameResult, Badge, BadgeType


class GameVoteSerializer(serializers.ModelSerializer):
    """Serializer for game votes."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = GameVote
        fields = [
            "id",
            "user_id",
            "user_email",
            "answer",
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "user_email", "created_at"]


class GameSerializer(serializers.ModelSerializer):
    """Serializer for games."""

    # Read-only fields
    public_id = serializers.UUIDField(read_only=True)
    event_id = serializers.IntegerField(source="event.id", read_only=True)
    created_by_id = serializers.IntegerField(source="created_by.id", read_only=True)
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    status = serializers.CharField(read_only=True)

    # Nested votes (filtered by current question)
    votes = serializers.SerializerMethodField()

    # Stats (computed)
    stats = serializers.SerializerMethodField()

    # Links
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "id",
            "public_id",
            "event_id",
            "created_by_id",
            "created_by_email",
            "game_type",
            "difficulty",
            "language_code",
            # Multi-question support
            "current_question_index",
            "total_questions",
            "answer_revealed",
            # Current question
            "question_id",
            "question_text",
            "correct_answer",
            "options",
            "context",
            "image_url",
            "status",
            "completed_at",
            "is_correct",
            "final_answer",
            "votes",
            "stats",
            "created_at",
            "updated_at",
            "_links",
        ]
        read_only_fields = [
            "id",
            "public_id",
            "event_id",
            "created_by_id",
            "created_by_email",
            "language_code",
            "current_question_index",
            "total_questions",
            "answer_revealed",
            "question_id",
            "question_text",
            "correct_answer",
            "options",
            "context",
            "image_url",
            "status",
            "completed_at",
            "is_correct",
            "final_answer",
            "votes",
            "stats",
            "created_at",
            "updated_at",
            "_links",
        ]

    def get_votes(self, obj):
        """Get votes for the current question only."""
        from games.models import GameVote
        votes = GameVote.objects.filter(
            game=obj,
            question_index=obj.current_question_index
        ).select_related('user')
        return GameVoteSerializer(votes, many=True).data

    def get_stats(self, obj):
        """Get game statistics."""
        from games.services import GameService
        return GameService.get_game_stats(obj)

    def get__links(self, obj):
        """Generate HATEOAS links."""
        request = self.context.get("request")
        if not request:
            return {}

        links = {
            "self": reverse("game-detail", kwargs={"pk": obj.pk}, request=request),
            "event": reverse("event-detail", kwargs={"pk": obj.event_id}, request=request),
        }

        # Add vote link if game is active
        if obj.status == "ACTIVE":
            links["vote"] = reverse("game-vote", kwargs={"pk": obj.pk}, request=request)

        return links


class GameCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a game.

    Note: The game automatically uses the event's language and difficulty.
    Only the game_type needs to be specified.
    """

    game_type = serializers.ChoiceField(choices=GameType.choices, required=True)

    def validate(self, attrs):
        """Validate game creation data."""
        return attrs


class VoteSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a vote."""

    answer = serializers.CharField(max_length=255, required=True)

    def validate_answer(self, value):
        """Validate answer is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Answer cannot be empty")
        return value.strip()


class GameStatsSerializer(serializers.Serializer):
    """Serializer for game statistics."""

    total_votes = serializers.IntegerField()
    confirmed_participants = serializers.IntegerField()
    vote_counts = serializers.DictField(child=serializers.IntegerField())
    votes_remaining = serializers.IntegerField()


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for badges."""

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Badge
        fields = [
            "id",
            "user_email",
            "badge_type",
            "earned_at",
        ]
        read_only_fields = ["id", "user_email", "badge_type", "earned_at"]


class GameResultSerializer(serializers.ModelSerializer):
    """Serializer for game results."""

    game_id = serializers.IntegerField(source="game.id", read_only=True)
    game_public_id = serializers.UUIDField(source="game.public_id", read_only=True)
    badges = BadgeSerializer(many=True, read_only=True)
    score_percentage = serializers.FloatField(read_only=True)
    victory_threshold = serializers.FloatField(read_only=True)

    class Meta:
        model = GameResult
        fields = [
            "id",
            "game_id",
            "game_public_id",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "badge_type",
            "victory_threshold",
            "badges",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "game_id",
            "game_public_id",
            "total_questions",
            "correct_answers",
            "score_percentage",
            "badge_type",
            "victory_threshold",
            "badges",
            "created_at",
        ]
