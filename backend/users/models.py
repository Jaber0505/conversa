"""User models for authentication and profiles."""
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils import timezone

from languages.models import Language
from common.constants import MINIMUM_USER_AGE, MAX_USER_BIO_LENGTH


class UserManager(BaseUserManager):
    """Custom manager for User model with email as username."""

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with email and password.

        Args:
            email: User's email address
            password: User's password (will be hashed)
            **extra_fields: Additional user fields

        Returns:
            User: Created user instance

        Raises:
            ValueError: If email or password is missing
        """
        if not email:
            raise ValueError("Email is required.")
        if not password:
            raise ValueError("Password is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with admin permissions.

        Args:
            email: Admin email address
            password: Admin password
            **extra_fields: Additional user fields

        Returns:
            User: Created superuser instance
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for language exchange platform.

    Uses email as username and includes language learning preferences,
    location data for event discovery, and GDPR consent tracking.
    """

    # Authentication
    email = models.EmailField(
        unique=True, db_index=True, help_text="User's email address (login)"
    )
    password = models.CharField(max_length=128, help_text="Hashed password")

    # Personal information
    first_name = models.CharField(max_length=150, help_text="User's first name")
    last_name = models.CharField(max_length=150, help_text="User's last name")
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(MINIMUM_USER_AGE)],
        help_text=f"User's age (minimum {MINIMUM_USER_AGE})",
    )

    # Profile
    bio = models.TextField(
        max_length=MAX_USER_BIO_LENGTH,
        blank=True,
        help_text=f"User biography (max {MAX_USER_BIO_LENGTH} characters)",
    )
    avatar = models.URLField(blank=True, help_text="Avatar image URL")

    # Location (for event discovery)
    address = models.CharField(
        max_length=255, blank=True, help_text="Street address"
    )
    city = models.CharField(max_length=100, blank=True, help_text="City")
    country = models.CharField(
        max_length=100, blank=True, help_text="Country code (e.g., BE)"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude for geolocation",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude for geolocation",
    )

    # Language preferences
    native_langs = models.ManyToManyField(
        Language,
        related_name="native_users",
        help_text="Languages the user speaks natively",
    )
    target_langs = models.ManyToManyField(
        Language,
        through="UserTargetLanguage",
        related_name="target_users",
        help_text="Languages the user wants to learn",
    )

    # GDPR compliance
    consent_given = models.BooleanField(
        default=False, help_text="User has given consent for data processing"
    )
    consent_given_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when consent was given"
    )

    # Account status
    is_active = models.BooleanField(
        default=True, help_text="User account is active"
    )
    is_staff = models.BooleanField(
        default=False, help_text="User can access admin site"
    )

    # Timestamps
    date_joined = models.DateTimeField(
        default=timezone.now, help_text="Date user joined the platform"
    )

    # Django auth configuration
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "age"]

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        constraints = [
            CheckConstraint(
                check=Q(age__gte=MINIMUM_USER_AGE),
                name="users_user_age_gte_18",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"


class UserTargetLanguage(models.Model):
    """
    Through model for User-Language many-to-many relationship.

    Allows future expansion for tracking learning progress per language.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="User learning the language"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, help_text="Language being learned"
    )

    # Future: Add fields like proficiency_level, started_at, etc.

    class Meta:
        unique_together = ("user", "language")
        verbose_name = "User Target Language"
        verbose_name_plural = "User Target Languages"
        ordering = ["user", "language"]

    def __str__(self):
        return f"{self.user.email} learning {self.language.label_en}"


class RevokedAccessToken(models.Model):
    """
    Denylist for revoked JWT access tokens.

    Stores JTI (JWT ID) of tokens that have been explicitly revoked
    (e.g., during logout) to prevent their reuse.
    """

    jti = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="JWT ID (jti claim) of the revoked token",
    )
    revoked_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when token was revoked"
    )

    class Meta:
        ordering = ["-revoked_at"]
        verbose_name = "Revoked Access Token"
        verbose_name_plural = "Revoked Access Tokens"

    def __str__(self):
        return f"Revoked {self.jti[:8]}... at {self.revoked_at}"
