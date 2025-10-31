"""
Scheduled tasks for the events application.

DEPRECATED: This file previously used Celery for async tasks.
Since we're using Render's free tier (which doesn't support Redis/Celery),
auto-cancellation is now handled via Django Management Commands + Render Cron Jobs:

1. Management Commands:
   - python manage.py cancel_underpopulated_events
   - python manage.py cleanup_expired_bookings

2. Render Cron Jobs Configuration (render.yaml):
   - cancel_underpopulated_events: Runs every 15 minutes
   - cleanup_expired_bookings: Runs every 10 minutes

This file is kept for reference but is no longer used in production.
For local development, you can still run the commands manually.

See: backend/events/management/commands/ for the new implementation.
"""
