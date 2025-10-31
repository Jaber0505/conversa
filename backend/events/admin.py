from django.contrib import admin
from django.utils import timezone
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "theme",
        "partner",
        "language",
        "datetime_start",
        "organizer",
        "status",
        "price_cents",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "language", "partner", "difficulty")
    search_fields = ("title", "theme", "partner__name", "language__code")
    ordering = ("-datetime_start",)
    readonly_fields = ("price_cents", "title", "address", "published_at", "cancelled_at", "created_at", "updated_at")
    actions = ["publish_events"]

    @admin.action(description="Publier les événements sélectionnés")
    def publish_events(self, request, queryset):
        """Publish selected events."""
        updated = queryset.filter(status=Event.Status.DRAFT).update(
            status=Event.Status.PUBLISHED,
            published_at=timezone.now()
        )
        self.message_user(
            request,
            f"{updated} événement(s) publié(s) avec succès.",
            level="SUCCESS"
        )

    publish_events.short_description = "Publier les événements sélectionnés"
