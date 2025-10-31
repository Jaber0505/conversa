"""
Tests for AuditService.

Tests all audit logging methods for different business events.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from audit.models import AuditLog
from audit.services import AuditService

User = get_user_model()


class AuditServiceTests(TestCase):
    """Test suite for AuditService methods."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )

    # ========================================================================
    # AUTH TESTS
    # ========================================================================

    def test_log_auth_login(self):
        """Test logging successful login."""
        log = AuditService.log_auth_login(
            user=self.user,
            ip="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        self.assertEqual(log.category, AuditLog.Category.AUTH)
        self.assertEqual(log.level, AuditLog.Level.INFO)
        self.assertEqual(log.action, "login_success")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip, "192.168.1.1")
        self.assertIn(self.user.email, log.message)

    def test_log_auth_login_failed(self):
        """Test logging failed login attempt."""
        log = AuditService.log_auth_login_failed(
            email="attacker@example.com",
            ip="192.168.1.1",
            reason="invalid_credentials"
        )

        self.assertEqual(log.category, AuditLog.Category.AUTH)
        self.assertEqual(log.level, AuditLog.Level.WARNING)
        self.assertEqual(log.action, "login_failed")
        self.assertIsNone(log.user)  # No user for failed login
        self.assertIn("attacker@example.com", log.message)

    def test_log_auth_logout(self):
        """Test logging logout."""
        log = AuditService.log_auth_logout(
            user=self.user,
            ip="192.168.1.1"
        )

        self.assertEqual(log.category, AuditLog.Category.AUTH)
        self.assertEqual(log.action, "logout")
        self.assertEqual(log.user, self.user)

    # ========================================================================
    # USER TESTS
    # ========================================================================

    def test_log_user_registered(self):
        """Test logging user registration."""
        new_user = User.objects.create_user(
            email="newuser@example.com",
            password="pass123",
            age=22,
            consent_given=True,
        )

        log = AuditService.log_user_registered(
            user=new_user,
            ip="192.168.1.1"
        )

        self.assertEqual(log.category, AuditLog.Category.USER)
        self.assertEqual(log.action, "user_registered")
        self.assertEqual(log.resource_type, "User")
        self.assertEqual(log.resource_id, new_user.id)

    def test_log_user_profile_updated(self):
        """Test logging profile update."""
        log = AuditService.log_user_profile_updated(
            user=self.user,
            updated_by=self.user,
            changed_fields=["first_name", "bio"]
        )

        self.assertEqual(log.category, AuditLog.Category.USER)
        self.assertEqual(log.action, "user_profile_updated")
        self.assertIn("changed_fields", log.metadata)
        self.assertEqual(log.metadata["changed_fields"], ["first_name", "bio"])

    def test_log_user_deactivated(self):
        """Test logging user deactivation."""
        admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpass",
            age=30,
            is_staff=True,
            consent_given=True,
        )

        log = AuditService.log_user_deactivated(
            user=self.user,
            deactivated_by=admin,
            reason="policy_violation"
        )

        self.assertEqual(log.category, AuditLog.Category.ADMIN)
        self.assertEqual(log.level, AuditLog.Level.WARNING)
        self.assertEqual(log.action, "user_deactivated")
        self.assertIn("reason", log.metadata)

    # ========================================================================
    # ERROR TESTS
    # ========================================================================

    def test_log_error(self):
        """Test logging system error."""
        log = AuditService.log_error(
            action="database_query_failed",
            message="Database query timeout",
            user=self.user,
            error_details={"query": "SELECT *", "timeout": 30}
        )

        self.assertEqual(log.category, AuditLog.Category.SYSTEM)
        self.assertEqual(log.level, AuditLog.Level.ERROR)
        self.assertTrue(log.is_error)
        self.assertIn("query", log.metadata)

    def test_log_critical(self):
        """Test logging critical event."""
        log = AuditService.log_critical(
            action="service_unavailable",
            message="Payment gateway unreachable",
            error_details={"gateway": "stripe", "attempts": 3}
        )

        self.assertEqual(log.level, AuditLog.Level.CRITICAL)
        self.assertTrue(log.is_error)

    # ========================================================================
    # METADATA TESTS
    # ========================================================================

    def test_metadata_stored_correctly(self):
        """Test that metadata is stored as JSON correctly."""
        metadata = {
            "event_id": 123,
            "participants": 5,
            "price": 7.00,
            "tags": ["python", "django"],
            "nested": {"key": "value"}
        }

        log = AuditService.log_error(
            action="test",
            message="test",
            error_details=metadata
        )

        self.assertEqual(log.metadata, metadata)
        self.assertIsInstance(log.metadata["tags"], list)
        self.assertIsInstance(log.metadata["nested"], dict)

    def test_null_metadata(self):
        """Test logs can be created without metadata."""
        log = AuditService.log_auth_logout(user=self.user)

        # Metadata should exist but only contain basic info
        self.assertIsNotNone(log.metadata)
        self.assertIn("user_id", log.metadata)

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_multiple_logs_same_user(self):
        """Test creating multiple logs for same user."""
        AuditService.log_auth_login(user=self.user, ip="192.168.1.1")
        AuditService.log_user_profile_updated(
            user=self.user,
            updated_by=self.user,
            changed_fields=["bio"]
        )
        AuditService.log_auth_logout(user=self.user, ip="192.168.1.1")

        user_logs = AuditLog.objects.filter(user=self.user)
        self.assertEqual(user_logs.count(), 3)

    def test_audit_log_queryable_by_category(self):
        """Test filtering logs by category."""
        AuditService.log_auth_login(user=self.user)
        AuditService.log_user_registered(user=self.user)
        AuditService.log_error(action="test", message="test")

        auth_logs = AuditLog.objects.filter(category=AuditLog.Category.AUTH)
        self.assertEqual(auth_logs.count(), 1)

        user_logs = AuditLog.objects.filter(category=AuditLog.Category.USER)
        self.assertEqual(user_logs.count(), 1)

        system_logs = AuditLog.objects.filter(category=AuditLog.Category.SYSTEM)
        self.assertEqual(system_logs.count(), 1)
