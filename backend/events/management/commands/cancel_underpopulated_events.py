"""
Django management command to cancel underpopulated events.
This replaces Celery tasks for Render free tier compatibility.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from events.services.event_service import EventService


class Command(BaseCommand):
    help = 'Cancel events with less than 3 participants, 1 hour before start time'

    def handle(self, *args, **options):
        """Execute the auto-cancellation logic."""
        self.stdout.write(
            self.style.WARNING(
                f'[{timezone.now()}] Starting auto-cancellation check...'
            )
        )

        try:
            cancelled_events = EventService.check_and_cancel_underpopulated_events()

            if cancelled_events:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully cancelled {len(cancelled_events)} underpopulated events:'
                    )
                )
                for event in cancelled_events:
                    self.stdout.write(
                        f'  - Event #{event.id}: {event.title} '
                        f'({event.participants_count} participants)'
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No events needed cancellation.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during auto-cancellation: {str(e)}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS(
                f'[{timezone.now()}] Auto-cancellation check completed.'
            )
        )
