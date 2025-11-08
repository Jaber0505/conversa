"""Payment models for Stripe integration."""
from django.db import models
from django.conf import settings
from django.core import validators


class Payment(models.Model):
    """
    Payment record for Stripe transactions.

    Tracks payment status and links to Stripe Checkout sessions.
    Stores raw Stripe events for audit purposes.
    """

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="User who made the payment",
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="Associated booking",
    )

    # Stripe identifiers
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Stripe Checkout Session ID",
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe Payment Intent ID",
    )

    # Payment details
    amount_cents = models.IntegerField(
        default=0,
        validators=[
            validators.MinValueValidator(
                -1000000,  # Allow negative values for refunds (up to -10,000 EUR)
                message="Amount cannot be less than -1,000,000 cents (-10,000 EUR)"
            ),
            validators.MaxValueValidator(
                1000000,  # Maximum 10,000 EUR per transaction
                message="Amount cannot exceed 1,000,000 cents (10,000 EUR)"
            )
        ],
        help_text="Payment amount in cents (negative for refunds)"
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
        validators=[
            validators.MinLengthValidator(3, message="Currency must be a 3-letter ISO code"),
            validators.MaxLengthValidator(3, message="Currency must be a 3-letter ISO code"),
            validators.RegexValidator(
                regex=r'^[A-Z]{3}$',
                message="Currency must be 3 uppercase letters (e.g., EUR, USD, GBP)"
            )
        ],
        help_text="Currency code (ISO 4217 - 3 letter code, e.g., EUR)"
    )
    status = models.CharField(
        max_length=12,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text="Payment status",
    )

    # Audit
    raw_event = models.JSONField(
        blank=True,
        null=True,
        help_text="Latest Stripe webhook event (for audit trail)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "payments"
        ordering = ["-created_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["stripe_checkout_session_id"]),
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["user", "booking"]),
        ]

    def __str__(self):
        return f"Payment#{self.id} {self.status} {self.amount_cents} {self.currency}"

    def __init__(self, *args, **kwargs):
        """
        Support legacy kwarg alias `stripe_session_id` for backward compatibility
        with older tests/usages expecting this name instead of
        `stripe_checkout_session_id`.
        """
        alias = kwargs.pop("stripe_session_id", None)
        super().__init__(*args, **kwargs)
        if alias and not getattr(self, "stripe_checkout_session_id", None):
            self.stripe_checkout_session_id = alias
