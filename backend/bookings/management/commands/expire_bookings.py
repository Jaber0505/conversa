"""
Management command to expire pending bookings.

Usage:
    python manage.py expire_bookings

To run automatically on Render.com:
1. Go to your Render dashboard
2. Navigate to your web service
3. Add a Cron Job:
   - Name: Expire Bookings
   - Command: python manage.py expire_bookings
   - Schedule: */5 * * * * (every 5 minutes)

Note: Render free tier supports cron jobs!
"""

from django.core.management.base import BaseCommand
from bookings.services import BookingService


class Command(BaseCommand):
    help = 'Expire PENDING bookings past their expiration time'

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write("Starting booking expiration process...")

        try:
            count = BookingService.auto_expire_bookings()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {count} booking(s)')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error expiring bookings: {str(e)}')
            )
            raise
