"""
Django management command to clean up expired bookings.
This replaces Celery tasks for Render free tier compatibility.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.services.booking_service import BookingService


class Command(BaseCommand):
    help = 'Clean up expired PENDING bookings that have passed their expiration time'

    def handle(self, *args, **options):
        """Execute the expired bookings cleanup logic."""
        self.stdout.write(
            self.style.WARNING(
                f'[{timezone.now()}] Starting expired bookings cleanup...'
            )
        )

        try:
            expired_count = BookingService.auto_expire_bookings()

            if expired_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully cleaned up {expired_count} expired booking(s).'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No expired bookings to clean up.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS(
                f'[{timezone.now()}] Expired bookings cleanup completed.'
            )
        )
