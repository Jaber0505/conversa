"""
Audit models for comprehensive activity tracking.

This module provides audit logging for both HTTP requests and business logic events.
Supports categorization, log levels, and JSON metadata for rich context.
"""
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Comprehensive audit log for tracking user actions and system events.

    Tracks both:
    - HTTP requests (via AuditMiddleware)
    - Business logic events (via AuditService)

    Examples:
        - User login/logout
        - Event creation/cancellation
        - Booking creation/cancellation
        - Payment processing
        - Admin actions (partner creation, user ban)
    """

    class Category(models.TextChoices):
        """Event categories for filtering and analysis."""
        HTTP = "HTTP", "HTTP Request"
        AUTH = "AUTH", "Authentication"
        EVENT = "EVENT", "Event Management"
        BOOKING = "BOOKING", "Booking Management"
        PAYMENT = "PAYMENT", "Payment Processing"
        PARTNER = "PARTNER", "Partner Management"
        USER = "USER", "User Management"
        ADMIN = "ADMIN", "Admin Action"
        SYSTEM = "SYSTEM", "System Event"

    class Level(models.TextChoices):
        """Log severity levels."""
        DEBUG = "DEBUG", "Debug"
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"
        CRITICAL = "CRITICAL", "Critical"

    # Core fields
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.HTTP,
        db_index=True,
        help_text="Event category for filtering"
    )
    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        default=Level.INFO,
        db_index=True,
        help_text="Log severity level"
    )
    action = models.CharField(
        max_length=100,
        help_text="Action performed (e.g., 'user_login', 'event_created', 'booking_cancelled')"
    )
    message = models.TextField(
        blank=True,
        help_text="Human-readable description of the event"
    )

    # User context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        help_text="User who performed the action (null for anonymous or system actions)"
    )

    # HTTP context (for HTTP category logs)
    method = models.CharField(
        max_length=8,
        blank=True,
        help_text="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    path = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Request path"
    )
    status_code = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code"
    )
    ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="User agent string"
    )
    duration_ms = models.PositiveIntegerField(
        default=0,
        help_text="Request duration in milliseconds"
    )

    # Business context (for business logic logs)
    resource_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of resource affected (e.g., 'Event', 'Booking', 'Payment')"
    )
    resource_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of the affected resource"
    )

    # Additional context (JSON for flexibility)
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional context data (before/after values, error details, etc.)"
    )

    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this log entry was created"
    )

    class Meta:
        app_label = "audit"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["level", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        if self.category == self.Category.HTTP:
            return f"[HTTP] {self.method} {self.path} ({self.status_code})"
        return f"[{self.category}] {self.action} by {self.user or 'System'}"

    @property
    def is_error(self):
        """Check if this log represents an error condition."""
        return self.level in (self.Level.ERROR, self.Level.CRITICAL)
