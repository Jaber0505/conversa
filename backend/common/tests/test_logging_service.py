"""
Tests for LoggingService.

Run with: python manage.py test common.tests.test_logging_service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from common.logging_service import LoggingService

User = get_user_model()


class LoggingServiceTest(TestCase):
    """Test LoggingService methods."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            age=25
        )

    def test_log_info(self):
        """Test info logging."""
        # Should not raise exception
        LoggingService.log_info(
            "Test info message",
            category="test",
            extra={"key": "value"}
        )

    def test_log_warning(self):
        """Test warning logging."""
        # Should not raise exception
        LoggingService.log_warning(
            "Test warning message",
            category="test",
            extra={"key": "value"}
        )

    def test_log_error(self):
        """Test error logging."""
        # Should not raise exception
        LoggingService.log_error(
            "Test error message",
            category="test",
            exception=ValueError("Test exception"),
            extra={"key": "value"},
            user=self.user
        )

    def test_log_validation_error(self):
        """Test validation error logging."""
        # Should not raise exception
        LoggingService.log_validation_error(
            "Validation failed",
            category="test",
            validation_errors={"field": "error message"},
            user=self.user
        )

    def test_log_event_creation_start(self):
        """Test event creation start logging."""
        # Should not raise exception
        LoggingService.log_event_creation_start(
            user=self.user,
            event_data={
                "datetime_start": "2025-12-01 14:00:00",
                "partner": None,
                "language": None
            }
        )
