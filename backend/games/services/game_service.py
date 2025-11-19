"""
Game business logic service.

Handles game creation, voting, validation, and lifecycle management.

ARCHITECTURE RULE:
This service is the SINGLE SOURCE OF TRUTH for all game business logic.
ALL business rules, validations, and state transitions MUST be here.

Business Rules:
- Only event organizer can create games
- Only confirmed participants can vote
- One vote per participant per game
- One active game per event at a time
- Majority vote wins (>=50% of votes)
- Games can only be created during active events
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from common.services.base import BaseService
from bookings.models import BookingStatus
from events.models import Event


class GameService(BaseService):
    """Service layer for Game business logic."""

    # Game content cache
    _game_content_cache: Dict[str, List[Dict]] = {}

    @staticmethod
    def _load_game_content(language_code: str, game_type: str) -> List[Dict]:
        """
        Load game content from JSON files.

        Args:
            language_code: Language code (fr, en, nl)
            game_type: Type of game (picture_description, word_association, etc.)

        Returns:
            List of game questions

        Raises:
            FileNotFoundError: If JSON file doesn't exist
        """
        cache_key = f"{language_code}_{game_type}"

        # Check cache first
        if cache_key in GameService._game_content_cache:
            return GameService._game_content_cache[cache_key]

        # Load from file
        base_path = Path(settings.BASE_DIR) / "fixtures" / "games"
        file_path = base_path / f"{game_type}_{language_code}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Game content file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        # Cache and return
        GameService._game_content_cache[cache_key] = content
        return content

    @staticmethod
    def _get_random_question(language_code: str, game_type: str, difficulty: str) -> Dict:
        """
        Get a random question for given parameters.

        Args:
            language_code: Language code
            game_type: Type of game
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            Random question dict

        Raises:
            ValidationError: If no questions available for criteria
        """
        questions = GameService._load_game_content(language_code, game_type)

        # Filter by difficulty
        filtered = [q for q in questions if q.get("difficulty") == difficulty]

        if not filtered:
            raise ValidationError({
                "difficulty": f"No questions available for {game_type} at {difficulty} level in {language_code}"
            })

        return random.choice(filtered)

    @staticmethod
    def _get_questions_by_difficulty(language_code: str, game_type: str, difficulty: str) -> List[Dict]:
        """
        Get ALL questions for given parameters (for multi-question games).

        Args:
            language_code: Language code
            game_type: Type of game
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            List of question dicts

        Raises:
            ValidationError: If no questions available for criteria
        """
        questions = GameService._load_game_content(language_code, game_type)

        # Filter by difficulty
        filtered = [q for q in questions if q.get("difficulty") == difficulty]

        if not filtered:
            raise ValidationError({
                "difficulty": f"No questions available for {game_type} at {difficulty} level in {language_code}"
            })

        # Shuffle questions for variety
        random.shuffle(filtered)
        return filtered

    @staticmethod
    def _validate_organizer_permission(event: Event, user) -> None:
        """
        Validate that user is the event organizer.

        Args:
            event: Event instance
            user: User attempting to create game

        Raises:
            PermissionDenied: If user is not organizer
        """
        if event.organizer_id != user.id and not user.is_staff:
            raise PermissionDenied("Only the event organizer can create games")

    @staticmethod
    def _validate_participant_permission(event: Event, user) -> None:
        """
        Validate that user is a confirmed participant.

        Args:
            event: Event instance
            user: User attempting to vote

        Raises:
            PermissionDenied: If user is not a confirmed participant
        """
        has_confirmed_booking = event.bookings.filter(
            user=user,
            status=BookingStatus.CONFIRMED
        ).exists()

        if not has_confirmed_booking:
            raise PermissionDenied("Only confirmed participants can vote")

    @staticmethod
    def _validate_no_active_game(event: Event) -> None:
        """
        Validate that event has no active game.

        Args:
            event: Event instance

        Raises:
            ValidationError: If event already has an active game
        """
        from games.models import GameStatus, Game

        active_game_exists = Game.objects.filter(
            event=event,
            status=GameStatus.ACTIVE
        ).exists()

        if active_game_exists:
            raise ValidationError({
                "event": "This event already has an active game. Complete the current game first."
            })

    @staticmethod
    def _validate_event_is_active(event: Event, skip_time_validation: bool = False) -> None:
        """
        Validate that event is currently active.

        Args:
            event: Event instance
            skip_time_validation: If True, skip time-based validations (for testing)

        Raises:
            ValidationError: If event is not active
        """
        from datetime import timedelta
        now = timezone.now()

        # Event must be published
        if event.status != Event.Status.PUBLISHED:
            raise ValidationError({
                "event": "Games can only be created for published events"
            })

        # Skip time validation if requested (for testing)
        if skip_time_validation:
            return

        # Event must have started (or be within 15 minutes of start)
        start_window = event.datetime_start - timedelta(minutes=15)
        if now < start_window:
            raise ValidationError({
                "event": "Games can only be created within 15 minutes before event starts"
            })

        # Event must not be finished (within event duration)
        if now > event.datetime_end:
            raise ValidationError({
                "event": "Games cannot be created after event has ended"
            })

    @staticmethod
    @transaction.atomic
    def create_game(
        event: Event,
        created_by,
        game_type: str,
        skip_time_validation: bool = False
    ):
        """
        Create a new game for an event.

        This loads ALL questions from the JSON file and creates a multi-question game.
        The organizer will control progression through questions.

        The game automatically uses the event's language and difficulty level.

        Args:
            event: Event to create game for
            created_by: User creating the game (must be organizer)
            game_type: Type of game
            skip_time_validation: If True, skip time-based validations (for testing)

        Returns:
            Game instance

        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user is not organizer
        """
        from games.models import Game

        # Validations
        GameService._validate_organizer_permission(event, created_by)
        GameService._validate_event_is_active(event, skip_time_validation)
        GameService._validate_no_active_game(event)

        # Get language and difficulty from event (automatic)
        language_code = event.language.code if hasattr(event.language, 'code') else 'en'
        difficulty = event.difficulty

        # Load ALL questions for this game type and difficulty
        all_questions = GameService._get_questions_by_difficulty(language_code, game_type, difficulty)

        # Get first question
        first_question = all_questions[0]

        # Create game with all questions loaded (no timeout - organizer controls progression)
        game = Game.objects.create(
            event=event,
            created_by=created_by,
            game_type=game_type,
            difficulty=difficulty,
            language_code=language_code,
            # Multi-question support
            questions_data=all_questions,
            total_questions=len(all_questions),
            current_question_index=0,
            # Current question (denormalized)
            question_id=first_question.get("id"),
            question_text=first_question.get("question"),
            correct_answer=first_question.get("correct_answer"),
            options=first_question.get("options", []),
            context=first_question.get("context"),
            image_url=first_question.get("image_url")
        )

        # Mark event as game started
        event.game_started = True
        event.save(update_fields=['game_started'])

        return game

    @staticmethod
    @transaction.atomic
    def submit_vote(game, user, answer: str):
        """
        Submit a vote for a game.

        Args:
            game: Game instance
            user: User submitting vote
            answer: Answer choice

        Returns:
            tuple: (GameVote instance, game_completed: bool)

        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user cannot vote
        """
        from games.models import GameVote, GameStatus

        # Validate game is active
        if game.status != GameStatus.ACTIVE:
            raise ValidationError({"game": "This game is no longer active"})

        # Validate user is confirmed participant
        GameService._validate_participant_permission(game.event, user)

        # Check if user already voted for this question
        existing_vote = GameVote.objects.filter(
            game=game,
            user=user,
            question_index=game.current_question_index
        ).first()
        if existing_vote:
            raise ValidationError({"vote": "You have already voted on this question"})

        # Validate answer is valid (must be one of the options)
        # Note: This validation should ideally check against available options
        # For now, we accept any answer

        # Create vote with question tracking
        vote = GameVote.objects.create(
            game=game,
            user=user,
            question_index=game.current_question_index,
            question_id=game.question_id,
            answer=answer
        )

        # Check if we should complete the game (majority reached)
        game_completed = GameService._check_and_complete_game(game)

        return vote, game_completed

    @staticmethod
    def _check_and_complete_game(game) -> bool:
        """
        Check if game should be completed based on votes.

        NOTE: In multi-question mode, this NO LONGER auto-completes.
        Instead, the organizer must explicitly call reveal_answer() and next_question().

        This method is kept for backward compatibility but now does nothing.

        Args:
            game: Game instance

        Returns:
            bool: Always False (no auto-completion)
        """
        # Multi-question games require explicit organizer control
        # No automatic completion
        return False

    @staticmethod
    def get_game_stats(game) -> Dict:
        """
        Get statistics for a game's current question.

        Args:
            game: Game instance

        Returns:
            Dict with vote counts and statistics for current question
        """
        from games.models import GameVote
        from collections import Counter

        # Get votes for current question only
        votes = GameVote.objects.filter(
            game=game,
            question_index=game.current_question_index
        ).values_list('answer', flat=True)
        vote_counts = dict(Counter(votes))

        confirmed_count = game.event.bookings.filter(
            status=BookingStatus.CONFIRMED
        ).count()

        total_votes = len(votes)

        return {
            "total_votes": total_votes,
            "confirmed_participants": confirmed_count,
            "vote_counts": vote_counts,
            "votes_remaining": max(0, confirmed_count - total_votes),
        }

    @staticmethod
    def get_active_game(event) -> Optional:
        """
        Get the active game for an event.

        Args:
            event: Event instance

        Returns:
            Game instance or None
        """
        from games.models import GameStatus, Game

        return Game.objects.filter(
            event=event,
            status=GameStatus.ACTIVE
        ).first()

    @staticmethod
    @transaction.atomic
    def reveal_answer(game, user):
        """
        Reveal the answer for the current question (organizer-only).

        This transitions the game to SHOWING_RESULTS status, calculates the
        majority vote, and determines if the team answered correctly.

        Args:
            game: Game instance
            user: User requesting reveal (must be organizer)

        Returns:
            Dict with reveal results

        Raises:
            PermissionDenied: If user is not organizer
            ValidationError: If game is not in ACTIVE status
        """
        from games.models import GameVote, GameStatus
        from collections import Counter

        # Validate organizer permission
        GameService._validate_organizer_permission(game.event, user)

        # Validate game is active
        if game.status != GameStatus.ACTIVE:
            raise ValidationError({"game": "Can only reveal answer for active games"})

        # Validate answer not already revealed
        if game.answer_revealed:
            raise ValidationError({"game": "Answer already revealed for this question"})

        # Get all votes for current question
        votes = GameVote.objects.filter(
            game=game,
            question_index=game.current_question_index
        ).values_list('answer', flat=True)
        total_votes = len(votes)

        if total_votes == 0:
            # No votes - mark as incorrect with no answer
            game.status = GameStatus.SHOWING_RESULTS
            game.answer_revealed = True
            game.is_correct = False
            game.final_answer = None
            game.save(update_fields=['status', 'answer_revealed', 'is_correct', 'final_answer', 'updated_at'])

            return {
                "status": "revealed",
                "correct_answer": game.correct_answer,
                "team_answer": None,
                "is_correct": False,
                "vote_counts": {},
                "total_votes": 0
            }

        # Calculate majority vote
        vote_counts = Counter(votes)
        most_common_answer, most_common_count = vote_counts.most_common(1)[0]
        is_correct = (most_common_answer == game.correct_answer)

        # Update game state
        game.status = GameStatus.SHOWING_RESULTS
        game.answer_revealed = True
        game.is_correct = is_correct
        game.final_answer = most_common_answer
        game.save(update_fields=['status', 'answer_revealed', 'is_correct', 'final_answer', 'updated_at'])

        return {
            "status": "revealed",
            "correct_answer": game.correct_answer,
            "team_answer": most_common_answer,
            "is_correct": is_correct,
            "vote_counts": dict(vote_counts),
            "total_votes": total_votes
        }

    @staticmethod
    @transaction.atomic
    def next_question(game, user):
        """
        Move to the next question or complete the game (organizer-only).

        This clears votes for the current question and loads the next question,
        or marks the game as completed if no more questions remain.

        Args:
            game: Game instance
            user: User requesting next question (must be organizer)

        Returns:
            Dict with next question info or completion status

        Raises:
            PermissionDenied: If user is not organizer
            ValidationError: If game is not in SHOWING_RESULTS status
        """
        from games.models import GameVote, GameStatus

        # Validate organizer permission
        GameService._validate_organizer_permission(game.event, user)

        # Validate game is showing results
        if game.status != GameStatus.SHOWING_RESULTS:
            raise ValidationError({"game": "Can only proceed to next question after revealing answer"})

        # Check if more questions remain
        next_index = game.current_question_index + 1

        if next_index >= game.total_questions:
            # No more questions - complete the game
            game.status = GameStatus.COMPLETED
            game.completed_at = timezone.now()
            game.save(update_fields=['status', 'completed_at', 'updated_at'])

            # Calculate and save final results with badges
            game_result = GameService._calculate_final_results(game)

            return {
                "status": "completed",
                "message": "All questions completed",
                "result": {
                    "total_questions": game_result.total_questions,
                    "correct_answers": game_result.correct_answers,
                    "score_percentage": float(game_result.score_percentage),
                    "badge_type": game_result.badge_type
                }
            }

        # Load next question
        next_question_data = game.questions_data[next_index]

        # NOTE: We no longer delete votes - they are preserved for game history
        # Each vote is tagged with question_index for tracking

        # Update game with next question
        game.current_question_index = next_index
        game.question_id = next_question_data.get("id")
        game.question_text = next_question_data.get("question")
        game.correct_answer = next_question_data.get("correct_answer")
        game.options = next_question_data.get("options", [])
        game.context = next_question_data.get("context")
        game.image_url = next_question_data.get("image_url")
        game.answer_revealed = False
        game.is_correct = None
        game.final_answer = None
        game.status = GameStatus.ACTIVE
        game.save(update_fields=[
            'current_question_index', 'question_id', 'question_text',
            'correct_answer', 'options', 'context', 'image_url', 'answer_revealed',
            'is_correct', 'final_answer', 'status', 'updated_at'
        ])

        return {
            "status": "next_question",
            "current_question": next_index + 1,
            "total_questions": game.total_questions,
            "question": {
                "id": game.question_id,
                "text": game.question_text,
                "image_url": game.image_url
            }
        }

    @staticmethod
    @transaction.atomic
    def _calculate_final_results(game):
        """
        Calculate final results for a completed game and award badges.

        This analyzes all questions and their outcomes to determine:
        - Total correct answers
        - Score percentage
        - Badge type (victory or participation)
        - Individual badges for all participants

        Args:
            game: Completed Game instance

        Returns:
            GameResult instance
        """
        from games.models import GameResult, Badge, BadgeType, GameVote
        from bookings.models import BookingStatus

        # Count correct answers across all questions
        correct_count = 0
        for question_data in game.questions_data:
            question_index = game.questions_data.index(question_data)
            question_correct_answer = question_data.get("correct_answer")

            # Get votes for this question
            votes = GameVote.objects.filter(
                game=game,
                question_index=question_index
            ).values_list('answer', flat=True)

            if votes:
                from collections import Counter
                vote_counts = Counter(votes)
                most_common_answer = vote_counts.most_common(1)[0][0]

                if most_common_answer == question_correct_answer:
                    correct_count += 1

        # Calculate score percentage
        total_questions = game.total_questions
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0

        # Determine badge type (victory if >= 50%)
        victory_threshold = 50.0
        badge_type = BadgeType.VICTORY if score_percentage >= victory_threshold else BadgeType.PARTICIPATION

        # Create or update game result
        game_result, created = GameResult.objects.get_or_create(
            game=game,
            defaults={
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'score_percentage': score_percentage,
                'badge_type': badge_type,
                'victory_threshold': victory_threshold
            }
        )

        if not created:
            # Update existing result
            game_result.total_questions = total_questions
            game_result.correct_answers = correct_count
            game_result.score_percentage = score_percentage
            game_result.badge_type = badge_type
            game_result.save()

        # Award badges to all confirmed participants
        confirmed_participants = game.event.bookings.filter(
            status=BookingStatus.CONFIRMED
        ).values_list('user', flat=True)

        for user_id in confirmed_participants:
            Badge.objects.get_or_create(
                game_result=game_result,
                user_id=user_id,
                defaults={'badge_type': badge_type}
            )

        return game_result

    @staticmethod
    def get_detailed_results(game) -> Dict:
        """
        Get detailed results for each question in a completed game.

        Returns vote details for each question including:
        - Question info (text, correct answer, options, context)
        - All votes with user details
        - Team's final answer (majority vote)
        - Whether team answered correctly

        Args:
            game: Completed Game instance

        Returns:
            Dict with detailed results per question
        """
        from games.models import GameVote
        from collections import Counter

        if game.status != 'COMPLETED':
            raise ValidationError({"game": "Results only available for completed games"})

        results_by_question = []

        for question_index, question_data in enumerate(game.questions_data):
            # Get all votes for this question
            votes = GameVote.objects.filter(
                game=game,
                question_index=question_index
            ).select_related('user')

            # Serialize votes
            votes_data = [
                {
                    "user_id": vote.user_id,
                    "user_email": vote.user.email,
                    "answer": vote.answer,
                    "created_at": vote.created_at.isoformat()
                }
                for vote in votes
            ]

            # Calculate majority answer
            vote_answers = [v.answer for v in votes]
            team_answer = None
            is_correct = False

            if vote_answers:
                vote_counts = Counter(vote_answers)
                team_answer = vote_counts.most_common(1)[0][0]
                is_correct = (team_answer == question_data.get("correct_answer"))

            results_by_question.append({
                "question_index": question_index,
                "question_id": question_data.get("id"),
                "question_text": question_data.get("question"),
                "image_url": question_data.get("image_url"),
                "options": question_data.get("options", []),
                "correct_answer": question_data.get("correct_answer"),
                "context": question_data.get("context"),
                "team_answer": team_answer,
                "is_correct": is_correct,
                "votes": votes_data,
                "total_votes": len(votes_data)
            })

        return {
            "game_id": game.id,
            "game_public_id": str(game.public_id),
            "total_questions": game.total_questions,
            "questions": results_by_question
        }
