"""Admin interface for games management."""

from django.contrib import admin
from .models import Game, GameVote


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin interface for Game model."""

    list_display = [
        "id",
        "public_id",
        "event",
        "game_type",
        "difficulty",
        "status",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "game_type", "difficulty", "created_at"]
    search_fields = ["public_id", "event__title", "created_by__username"]
    readonly_fields = [
        "public_id",
        "completed_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "public_id",
                    "event",
                    "created_by",
                    "game_type",
                    "difficulty",
                    "language_code",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "question_id",
                    "question_text",
                    "correct_answer",
                    "image_url",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "completed_at",
                    "is_correct",
                    "final_answer",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(GameVote)
class GameVoteAdmin(admin.ModelAdmin):
    """Admin interface for GameVote model."""

    list_display = ["id", "game", "user", "answer", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["game__public_id", "user__username", "answer"]
    readonly_fields = ["created_at"]
