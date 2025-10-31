"""
Tests for Audit models.

Tests the AuditLog model including all categories, levels, and helper methods.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from audit.models import AuditLog

User = get_user_model()


class AuditLogModelTests(TestCase):
    """Test suite for AuditLog model."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )

    def test_create_http_log(self):
        """Test creating HTTP request log."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.INFO,
            action="GET /api/v1/events/",
            message="GET /api/v1/events/ → 200 (45ms)",
            user=self.user,
            method="GET",
            path="/api/v1/events/",
            status_code=200,
            duration_ms=45,
            ip="192.168.1.1",
        )

        self.assertEqual(log.category, AuditLog.Category.HTTP)
        self.assertEqual(log.level, AuditLog.Level.INFO)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.status_code, 200)
        self.assertFalse(log.is_error)

    def test_create_auth_log(self):
        """Test creating authentication log."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.AUTH,
            level=AuditLog.Level.INFO,
            action="login_success",
            message=f"User {self.user.email} logged in successfully",
            user=self.user,
            ip="192.168.1.1",
            metadata={"email": self.user.email, "user_id": self.user.id}
        )

        self.assertEqual(log.category, AuditLog.Category.AUTH)
        self.assertIsNotNone(log.metadata)
        self.assertEqual(log.metadata["email"], self.user.email)

    def test_create_business_log_with_resource(self):
        """Test creating business log with resource tracking."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.EVENT,
            level=AuditLog.Level.INFO,
            action="event_created",
            message="Event 'Python Meetup' created",
            user=self.user,
            resource_type="Event",
            resource_id=123,
            metadata={
                "event_id": 123,
                "theme": "Python Meetup",
                "partner_capacity": 50,
            }
        )

        self.assertEqual(log.category, AuditLog.Category.EVENT)
        self.assertEqual(log.resource_type, "Event")
        self.assertEqual(log.resource_id, 123)
        self.assertIn("theme", log.metadata)

    def test_create_error_log(self):
        """Test creating error log."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.ERROR,
            action="payment_processing_failed",
            message="Payment processing failed: Insufficient funds",
            user=self.user,
            metadata={"error": "Insufficient funds", "amount": 700}
        )

        self.assertEqual(log.level, AuditLog.Level.ERROR)
        self.assertTrue(log.is_error)

    def test_create_critical_log(self):
        """Test creating critical log."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.CRITICAL,
            action="database_connection_lost",
            message="Critical: Database connection lost",
            metadata={"error_details": "Connection timeout"}
        )

        self.assertEqual(log.level, AuditLog.Level.CRITICAL)
        self.assertTrue(log.is_error)

    def test_str_method_http(self):
        """Test __str__ method for HTTP logs."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.INFO,
            action="GET /api/v1/events/",
            method="GET",
            path="/api/v1/events/",
            status_code=200,
        )

        str_repr = str(log)
        self.assertIn("HTTP", str_repr)
        self.assertIn("GET", str_repr)
        self.assertIn("/api/v1/events/", str_repr)
        self.assertIn("200", str_repr)

    def test_str_method_business(self):
        """Test __str__ method for business logs."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.EVENT,
            level=AuditLog.Level.INFO,
            action="event_created",
            message="Event created",
            user=self.user,
        )

        str_repr = str(log)
        self.assertIn("EVENT", str_repr)
        self.assertIn("event_created", str_repr)
        self.assertIn(self.user.email, str_repr)

    def test_str_method_system(self):
        """Test __str__ method for system logs without user."""
        log = AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.INFO,
            action="scheduled_task_completed",
            message="Scheduled cleanup completed",
        )

        str_repr = str(log)
        self.assertIn("SYSTEM", str_repr)
        self.assertIn("scheduled_task_completed", str_repr)
        self.assertIn("System", str_repr)

    def test_is_error_property(self):
        """Test is_error property for different levels."""
        info_log = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.INFO,
            action="test",
        )
        self.assertFalse(info_log.is_error)

        warning_log = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.WARNING,
            action="test",
        )
        self.assertFalse(warning_log.is_error)

        error_log = AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.ERROR,
            action="test",
        )
        self.assertTrue(error_log.is_error)

        critical_log = AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.CRITICAL,
            action="test",
        )
        self.assertTrue(critical_log.is_error)

    def test_ordering(self):
        """Test default ordering (newest first)."""
        log1 = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.INFO,
            action="test1",
        )
        log2 = AuditLog.objects.create(
            category=AuditLog.Category.HTTP,
            level=AuditLog.Level.INFO,
            action="test2",
        )

        logs = list(AuditLog.objects.all())
        self.assertEqual(logs[0].id, log2.id)  # Newest first
        self.assertEqual(logs[1].id, log1.id)

    def test_all_categories_valid(self):
        """Test all category choices are valid."""
        for category_code, category_label in AuditLog.Category.choices:
            log = AuditLog.objects.create(
                category=category_code,
                level=AuditLog.Level.INFO,
                action=f"test_{category_code}",
            )
            self.assertEqual(log.category, category_code)

    def test_all_levels_valid(self):
        """Test all level choices are valid."""
        for level_code, level_label in AuditLog.Level.choices:
            log = AuditLog.objects.create(
                category=AuditLog.Category.SYSTEM,
                level=level_code,
                action=f"test_{level_code}",
            )
            self.assertEqual(log.level, level_code)
