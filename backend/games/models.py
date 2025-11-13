"""
Game models for Conversa events.

This module defines models for interactive language learning games
that can be played during events.
"""

import uuid
from django.conf import settings
from django.core import validators
from django.db import models
from django.utils import timezone


class GameType(models.TextChoices):
    """Available game types."""
    PICTURE_DESCRIPTION = "picture_description", "Picture Description"
    WORD_ASSOCIATION = "word_association", "Word Association"
    DEBATE = "debate", "Debate"
    ROLE_PLAY = "role_play", "Role Play"


class GameDifficulty(models.TextChoices):
    """Game difficulty levels."""
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class GameStatus(models.TextChoices):
    """Game lifecycle status."""
    ACTIVE = "ACTIVE", "Active"
    SHOWING_RESULTS = "SHOWING_RESULTS", "Showing Results"
    COMPLETED = "COMPLETED", "Completed"


class Game(models.Model):
    """
    Game instance for an event.

    A game is created by the event organizer during the event.
    Participants vote collaboratively on answers.

    Business Rules:
    - Only event organizer can create games
    - Only confirmed participants can vote
    - Majority vote determines the answer
    - One active game per event at a time
    """

    # Public identifier
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Public UUID for external references"
    )

    # Relationships
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="games",
        help_text="Event this game belongs to"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_games",
        help_text="Organizer who created this game"
    )

    # Game configuration
    game_type = models.CharField(
        max_length=32,
        choices=GameType.choices,
        help_text="Type of game"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=GameDifficulty.choices,
        help_text="Difficulty level"
    )
    language_code = models.CharField(
        max_length=5,
        help_text="Language code (fr, en, nl) from event language"
    )

    # Multi-question game support
    current_question_index = models.PositiveIntegerField(
        default=0,
        help_text="Current question index in the game (0-based)"
    )
    total_questions = models.PositiveIntegerField(
        default=1,
        help_text="Total number of questions loaded from JSON"
    )
    questions_data = models.JSONField(
        default=list,
        help_text="All questions loaded from JSON file"
    )

    # Current question (denormalized for performance)
    question_id = models.CharField(
        max_length=50,
        help_text="ID of the current question from JSON file"
    )
    question_text = models.TextField(
        help_text="The current question text"
    )
    correct_answer = models.CharField(
        max_length=255,
        help_text="Correct answer key for current question"
    )
    options = models.JSONField(
        default=list,
        help_text="Answer options for current question"
    )
    context = models.TextField(
        blank=True,
        null=True,
        help_text="Explanation or context for current question"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional image URL for current question"
    )
    answer_revealed = models.BooleanField(
        default=False,
        help_text="Whether the answer has been revealed by organizer"
    )

    # Status (controlled by organizer, no auto-timeout)
    status = models.CharField(
        max_length=16,
        choices=GameStatus.choices,
        default=GameStatus.ACTIVE,
        db_index=True,
        help_text="Current game status"
    )

    # Completion tracking
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When game was completed"
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether team answered correctly"
    )
    final_answer = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Final answer chosen by majority vote"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event", "status"]),
        ]
        verbose_name = "Game"
        verbose_name_plural = "Games"

    def __str__(self):
        return f"Game {self.public_id} - {self.game_type} ({self.status})"

    def mark_completed(self, is_correct: bool, final_answer: str):
        """
        Mark game as completed with result.

        Args:
            is_correct: Whether answer was correct
            final_answer: The chosen answer
        """
        self.status = GameStatus.COMPLETED
        self.completed_at = timezone.now()
        self.is_correct = is_correct
        self.final_answer = final_answer
        self.save(update_fields=["status", "completed_at", "is_correct", "final_answer", "updated_at"])

class GameVote(models.Model):
    """
    Individual participant vote for a game.

    Each confirmed participant can vote once per question.
    The majority vote determines the final answer.

    Business Rules:
    - One vote per participant per question
    - Only CONFIRMED participants can vote
    - Votes are immutable (cannot change after submission)
    - Votes are preserved for game history/results
    """

    # Relationships
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="votes",
        help_text="Game being voted on"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_votes",
        help_text="User who voted"
    )

    # Question tracking
    question_index = models.PositiveIntegerField(
        default=0,
        help_text="Index of the question this vote is for (0-based)"
    )
    question_id = models.CharField(
        max_length=50,
        default="unknown",
        help_text="ID of the question from JSON file"
    )

    # Vote content
    answer = models.CharField(
        max_length=255,
        help_text="The answer this user voted for"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "user", "question_index"],
                name="unique_vote_per_user_per_question"
            )
        ]
        indexes = [
            models.Index(fields=["game", "question_index"]),
            models.Index(fields=["game", "answer"]),
        ]
        verbose_name = "Game Vote"
        verbose_name_plural = "Game Votes"

    def __str__(self):
        return f"Vote by {self.user} on Game {self.game.public_id} Q{self.question_index}"


class BadgeType(models.TextChoices):
    """Types of badges that can be earned."""
    VICTORY = "victory", "Victory"
    PARTICIPATION = "participation", "Participation"


class GameResult(models.Model):
    """
    Final result for a completed game.

    Stores the overall team performance and badge earned.
    """

    # Relationships
    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        related_name="result",
        help_text="Game this result is for"
    )

    # Score tracking
    total_questions = models.PositiveIntegerField(
        help_text="Total number of questions in game"
    )
    correct_answers = models.PositiveIntegerField(
        default=0,
        help_text="Number of questions answered correctly"
    )
    score_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of correct answers (0-100)"
    )

    # Badge earned
    badge_type = models.CharField(
        max_length=20,
        choices=BadgeType.choices,
        help_text="Type of badge earned"
    )

    # Victory threshold (configurable per game)
    victory_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.0,
        help_text="Percentage needed for victory badge (default 50%)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Game Result"
        verbose_name_plural = "Game Results"

    def __str__(self):
        return f"Result for Game {self.game.public_id} - {self.badge_type}"


class Badge(models.Model):
    """
    Badge earned by a user for game participation/victory.

    Each participant gets their own badge record.
    """

    # Relationships
    game_result = models.ForeignKey(
        GameResult,
        on_delete=models.CASCADE,
        related_name="badges",
        help_text="Game result this badge is from"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_badges",
        help_text="User who earned this badge"
    )

    # Badge details
    badge_type = models.CharField(
        max_length=20,
        choices=BadgeType.choices,
        help_text="Type of badge earned"
    )

    # Timestamps
    earned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-earned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["game_result", "user"],
                name="unique_badge_per_user_per_game"
            )
        ]
        indexes = [
            models.Index(fields=["user", "badge_type"]),
        ]
        verbose_name = "Badge"
        verbose_name_plural = "Badges"

    def __str__(self):
        return f"{self.badge_type} badge for {self.user.email} - Game {self.game_result.game.public_id}"
