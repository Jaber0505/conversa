"""
API views for game management.

This module provides RESTful endpoints for creating games,
submitting votes, and retrieving game statistics.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from common.permissions import IsAuthenticatedAndActive
from events.models import Event
from .models import Game, GameVote, GameStatus, GameResult
from .serializers import (
    GameSerializer,
    GameCreateSerializer,
    VoteSubmitSerializer,
    GameStatsSerializer,
    GameResultSerializer,
)
from .services import GameService


@extend_schema_view(
    list=extend_schema(
        tags=["Games"],
        summary="List games for an event",
        description=(
            "List all games for a specific event.\n\n"
            "**Access:**\n"
            "- Confirmed participants can see all games for their events\n"
            "- Organizers can see all games for their events\n"
            "- Staff can see all games\n"
        ),
        parameters=[
            OpenApiParameter(
                name="event_id",
                description="Filter by event ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="status",
                description="Filter by game status (ACTIVE, SHOWING_RESULTS, COMPLETED)",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: GameSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
    retrieve=extend_schema(
        tags=["Games"],
        summary="Get game details",
        description="Retrieve details of a specific game including votes and statistics.",
        responses={
            200: GameSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Game not found"),
        },
    ),
)
class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for game management.

    Provides endpoints for:
    - Listing games
    - Retrieving game details
    - Creating games (custom action)
    - Submitting votes (custom action)
    - Getting statistics (custom action)
    """

    queryset = Game.objects.all().select_related(
        "event", "created_by"
    ).prefetch_related("votes", "votes__user")
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        Users can see games for:
        - Events they are confirmed participants in
        - Events they organized
        - All events (if staff)
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Staff can see all games
        if user.is_staff:
            return queryset

        # Filter by events user has access to
        from bookings.models import BookingStatus
        from django.db.models import Q

        accessible_events = Event.objects.filter(
            Q(organizer=user) |  # Events user organized
            Q(bookings__user=user, bookings__status=BookingStatus.CONFIRMED)  # Events user is confirmed participant
        ).distinct()

        queryset = queryset.filter(event__in=accessible_events)

        # Apply filters
        event_id = self.request.query_params.get("event_id")
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset

    @extend_schema(
        tags=["Games"],
        summary="Create a game",
        description=(
            "Create a new game for an event.\n\n"
            "**Rules:**\n"
            "- Only event organizer can create games\n"
            "- Event must be active (started, not finished)\n"
            "- Only one active game per event at a time\n\n"
            "**Process:**\n"
            "1. System selects random question based on type/difficulty\n"
            "2. Game becomes active with countdown timer\n"
            "3. Participants can vote until majority reached\n"
        ),
        request=GameCreateSerializer,
        responses={
            201: GameSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
        },
    )
    @action(detail=False, methods=["post"], url_path="create")
    def create_game(self, request):
        """Create a new game for an event."""
        serializer = GameCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get event from request data
        event_id = request.data.get("event_id")
        if not event_id:
            raise ValidationError({"event_id": "Event ID is required"})

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise NotFound("Event not found")

        # Create game via service (uses event's language and difficulty automatically)
        try:
            game = GameService.create_game(
                event=event,
                created_by=request.user,
                game_type=serializer.validated_data["game_type"],
                skip_time_validation=serializer.validated_data.get("skip_time_validation", False)
            )
        except (ValidationError, PermissionDenied) as e:
            raise e
        except FileNotFoundError as e:
            raise ValidationError({"game_content": str(e)})

        # Return serialized game
        response_serializer = GameSerializer(game, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Games"],
        summary="Submit a vote",
        description=(
            "Submit a vote for an active game.\n\n"
            "**Rules:**\n"
            "- Only confirmed participants can vote\n"
            "- One vote per participant per game\n"
            "- Game must be ACTIVE\n\n"
            "**Auto-completion:**\n"
            "- Game completes when all participants vote\n"
            "- Game completes when majority (>50%) vote for same answer\n"
        ),
        request=VoteSubmitSerializer,
        responses={
            201: GameSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Game not found"),
        },
    )
    @action(detail=True, methods=["post"], url_path="vote")
    def vote(self, request, pk=None):
        """Submit a vote for a game."""
        game = self.get_object()

        serializer = VoteSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Submit vote via service
        try:
            vote, game_completed = GameService.submit_vote(
                game=game,
                user=request.user,
                answer=serializer.validated_data["answer"],
            )
        except (ValidationError, PermissionDenied) as e:
            raise e

        # Refresh game to get updated status
        game.refresh_from_db()

        # Return updated game
        response_serializer = GameSerializer(game, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Games"],
        summary="Get game statistics",
        description=(
            "Get real-time statistics for a game.\n\n"
            "**Returns:**\n"
            "- Total votes submitted\n"
            "- Vote distribution by answer\n"
            "- Remaining votes needed\n"
            "- Time remaining (seconds)\n"
        ),
        responses={
            200: GameStatsSerializer,
            404: OpenApiResponse(description="Game not found"),
        },
    )
    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        """Get statistics for a game."""
        game = self.get_object()
        stats = GameService.get_game_stats(game)

        serializer = GameStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Games"],
        summary="Get active game for event",
        description=(
            "Get the currently active game for an event.\n\n"
            "**Returns:**\n"
            "- Active game if one exists\n"
            "- 404 if no active game\n"
        ),
        parameters=[
            OpenApiParameter(
                name="event_id",
                description="Event ID",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: GameSerializer,
            404: OpenApiResponse(description="No active game found"),
        },
    )
    @action(detail=False, methods=["get"], url_path="active")
    def active_game(self, request):
        """Get the active game for an event."""
        from django.utils import timezone
        from bookings.models import BookingStatus

        event_id = request.query_params.get("event_id")
        if not event_id:
            raise ValidationError({"event_id": "Event ID is required"})

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise NotFound("Event not found")

        game = GameService.get_active_game(event)
        if not game:
            raise NotFound("No active game for this event")

        # Check user has access to this event
        queryset = self.get_queryset()
        if not queryset.filter(pk=game.pk).exists():
            raise PermissionDenied("You do not have access to this event")

        # Verify event has started (except for organizer)
        # Si le jeu est déjà lancé (game_started=True), on autorise l'accès
        # car cela signifie que l'organisateur a utilisé le mode test
        is_organizer = event.organizer_id == request.user.id
        now = timezone.now()

        if not is_organizer and now < event.datetime_start and not event.game_started:
            raise PermissionDenied("Event has not started yet. Only the organizer can access the game before event start.")

        # Verify user has confirmed booking (except for organizer)
        if not is_organizer:
            has_confirmed_booking = event.bookings.filter(
                user=request.user,
                status=BookingStatus.CONFIRMED
            ).exists()

            if not has_confirmed_booking:
                raise PermissionDenied("You must have a confirmed booking to access this game")

        serializer = GameSerializer(game, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        tags=["Games"],
        summary="Reveal answer (organizer only)",
        description=(
            "Reveal the correct answer for the current question.\n\n"
            "**Rules:**\n"
            "- Only event organizer can reveal answers\n"
            "- Game must be in ACTIVE status\n"
            "- Answer cannot already be revealed\n\n"
            "**Process:**\n"
            "1. Calculates majority vote from all participants\n"
            "2. Determines if team answered correctly\n"
            "3. Transitions game to SHOWING_RESULTS status\n"
            "4. Returns vote statistics and correctness\n"
        ),
        responses={
            200: OpenApiResponse(description="Answer revealed successfully"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied - organizer only"),
            404: OpenApiResponse(description="Game not found"),
        },
    )
    @action(detail=True, methods=["post"], url_path="reveal-answer")
    def reveal_answer(self, request, pk=None):
        """Reveal the answer for current question (organizer only)."""
        game = self.get_object()

        try:
            result = GameService.reveal_answer(game=game, user=request.user)
        except (ValidationError, PermissionDenied) as e:
            raise e

        # Refresh game to get updated status
        game.refresh_from_db()

        # Return result with updated game
        response_serializer = GameSerializer(game, context={"request": request})
        return Response({
            "game": response_serializer.data,
            "reveal": result
        })

    @extend_schema(
        tags=["Games"],
        summary="Next question (organizer only)",
        description=(
            "Move to the next question or complete the game.\n\n"
            "**Rules:**\n"
            "- Only event organizer can proceed to next question\n"
            "- Game must be in SHOWING_RESULTS status\n"
            "- Answer must have been revealed first\n\n"
            "**Process:**\n"
            "1. Clears votes from current question\n"
            "2. Loads next question from questions_data\n"
            "3. Transitions game back to ACTIVE status\n"
            "4. OR completes game if no more questions remain\n"
        ),
        responses={
            200: OpenApiResponse(description="Moved to next question or completed"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied - organizer only"),
            404: OpenApiResponse(description="Game not found"),
        },
    )
    @action(detail=True, methods=["post"], url_path="next-question")
    def next_question(self, request, pk=None):
        """Move to next question or complete game (organizer only)."""
        game = self.get_object()

        try:
            result = GameService.next_question(game=game, user=request.user)
        except (ValidationError, PermissionDenied) as e:
            raise e

        # Refresh game to get updated status
        game.refresh_from_db()

        # Return result with updated game
        response_serializer = GameSerializer(game, context={"request": request})
        return Response({
            "game": response_serializer.data,
            "next": result
        })

    @extend_schema(
        tags=["Games"],
        summary="Get detailed results per question",
        description=(
            "Get detailed results for each question in a completed game.\n\n"
            "**Returns:**\n"
            "- Question details (text, options, correct answer, context)\n"
            "- All votes with user details for each question\n"
            "- Team's answer (majority vote) per question\n"
            "- Whether team answered correctly per question\n\n"
            "**Access:**\n"
            "- Confirmed participants of the event\n"
            "- Event organizer\n"
            "- Staff\n\n"
            "**Rules:**\n"
            "- Game must be in COMPLETED status\n"
        ),
        responses={
            200: OpenApiResponse(description="Detailed results returned"),
            400: OpenApiResponse(description="Game not completed yet"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Game not found"),
        },
    )
    @action(detail=True, methods=["get"], url_path="detailed-results")
    def detailed_results(self, request, pk=None):
        """Get detailed results for each question in a completed game."""
        game = self.get_object()

        try:
            results = GameService.get_detailed_results(game=game)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(results)

    @extend_schema(
        tags=["Games"],
        summary="Get game summary with badges",
        description=(
            "Get final summary for a completed game.\n\n"
            "**Returns:**\n"
            "- Total questions and correct answers\n"
            "- Score percentage\n"
            "- Badge type earned (victory or participation)\n"
            "- List of all participants who earned badges\n\n"
            "**Access:**\n"
            "- Confirmed participants of the event\n"
            "- Event organizer\n"
            "- Staff\n\n"
            "**Rules:**\n"
            "- Game must be in COMPLETED status\n"
            "- Results must have been calculated\n"
        ),
        responses={
            200: GameResultSerializer,
            404: OpenApiResponse(description="Game or results not found"),
        },
    )
    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        """Get final summary with badges for a completed game."""
        game = self.get_object()

        try:
            game_result = GameResult.objects.select_related('game').prefetch_related(
                'badges', 'badges__user'
            ).get(game=game)
        except GameResult.DoesNotExist:
            return Response(
                {"detail": "Results not yet calculated for this game"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GameResultSerializer(game_result, context={"request": request})
        return Response(serializer.data)
