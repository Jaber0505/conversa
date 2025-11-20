"""
Django management command to automatically finish completed events.

Usage:
    python manage.py auto_finish_events

This command is designed to run periodically via Render Cron Jobs.
It marks events as FINISHED when:
- Event started more than 1 hour ago
- No active game is running (game COMPLETED or no game)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.services import EventService


class Command(BaseCommand):
    help = "Automatically finish events that have completed (1h after start)"

    def handle(self, *args, **options):
        """Execute the auto-finish logic."""
        try:
            self.stdout.write(
                f'[{timezone.now()}] Starting auto-finish check...'
            )

            finished_count = EventService.auto_finish_completed_events()

            if finished_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Finished {finished_count} completed event(s)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        '✓ No events to finish'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during auto-finish: {str(e)}')
            )
            raise

        finally:
            self.stdout.write(
                f'[{timezone.now()}] Auto-finish check completed.'
            )
