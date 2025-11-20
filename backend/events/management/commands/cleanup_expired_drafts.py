"""
Django management command to clean up expired DRAFT events.

Usage:
    python manage.py cleanup_expired_drafts

This command is designed to run periodically via Render Cron Jobs.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.services import EventService


class Command(BaseCommand):
    help = "Delete DRAFT events whose datetime_start has passed"

    def handle(self, *args, **options):
        """Execute the cleanup logic."""
        try:
            self.stdout.write(
                f'[{timezone.now()}] Starting DRAFT cleanup...'
            )

            deleted_count = EventService.cleanup_expired_drafts()

            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Cleaned up {deleted_count} expired DRAFT event(s)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        '✓ No expired DRAFT events to clean up'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            raise

        finally:
            self.stdout.write(
                f'[{timezone.now()}] DRAFT cleanup completed.'
            )
