"""
User service for user management business logic.

Handles user creation, profile updates, and user-related operations.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from common.services.base import BaseService
from common.constants import (
    MINIMUM_USER_AGE,
    REQUIRED_NATIVE_LANGUAGES,
    REQUIRED_TARGET_LANGUAGES,
)

User = get_user_model()

# Whitelist of fields that can be updated via update_user_profile
ALLOWED_PROFILE_FIELDS = {
    "first_name",
    "last_name",
    "bio",
    "avatar",
    "address",
    "city",
    "country",
    "latitude",
    "longitude",
}


class UserService(BaseService):
    """
    User management business logic.

    Handles user registration, profile updates, and related operations.
    """

    @staticmethod
    @transaction.atomic
    def create_user(
        email,
        password,
        first_name,
        last_name,
        age,
        native_langs,
        target_langs,
        consent_given,
        **extra_fields,
    ):
        """
        Create a new user with language preferences.

        Args:
            email: User's email address
            password: User's password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            age: User's age (must be >= MINIMUM_USER_AGE)
            native_langs: List of Language objects (native languages)
            target_langs: List of Language objects (target languages)
            consent_given: GDPR consent flag
            **extra_fields: Additional user fields (bio, avatar, etc.)

        Returns:
            User: Created user instance

        Raises:
            ValidationError: If validation fails
        """
        if age < MINIMUM_USER_AGE:
            raise ValidationError({"age": f"Age must be at least {MINIMUM_USER_AGE}"})

        if len(native_langs) < REQUIRED_NATIVE_LANGUAGES:
            raise ValidationError(
                {
                    "native_langs": f"At least {REQUIRED_NATIVE_LANGUAGES} native language(s) required"
                }
            )

        if len(target_langs) < REQUIRED_TARGET_LANGUAGES:
            raise ValidationError(
                {
                    "target_langs": f"At least {REQUIRED_TARGET_LANGUAGES} target language(s) required"
                }
            )

        if not consent_given:
            raise ValidationError({"consent_given": "User consent is required"})

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            age=age,
            is_active=True,
            consent_given=bool(consent_given),
            consent_given_at=timezone.now() if consent_given else None,
            **extra_fields,
        )

        user.native_langs.set(native_langs)
        user.target_langs.set(target_langs)

        return user

    @staticmethod
    def update_user_profile(user, **fields):
        """
        Update user profile fields (whitelisted only).

        Args:
            user: User instance to update
            **fields: Fields to update (only allowed fields will be applied)

        Returns:
            User: Updated user instance

        Raises:
            ValidationError:
                - If any business rule fails during update.
                - If at least one provided field is not part of ALLOWED_PROFILE_FIELDS.
                  Frontends should catch this error and surface the message so that users
                  know which fields are rejected.

        Note:
            Only fields in ALLOWED_PROFILE_FIELDS can be updated.
            Sensitive fields like is_staff, is_superuser, password are blocked.
        """
        unauthorized_fields = set(fields.keys()) - ALLOWED_PROFILE_FIELDS
        if unauthorized_fields:
            raise ValidationError(
                {
                    "fields": f"Cannot update these fields: {', '.join(sorted(unauthorized_fields))}"
                }
            )

        for field, value in fields.items():
            setattr(user, field, value)

        user.save()
        return user

    @staticmethod
    def update_user_languages(user, native_langs=None, target_langs=None):
        """
        Update user's language preferences.

        Args:
            user: User instance
            native_langs: List of Language objects (optional)
            target_langs: List of Language objects (optional)

        Returns:
            User: Updated user instance
        """
        if native_langs is not None:
            user.native_langs.set(native_langs)

        if target_langs is not None:
            user.target_langs.set(target_langs)

        return user

    @staticmethod
    def deactivate_user(user):
        """Deactivate a user account."""
        user.is_active = False
        user.save()
        return user

    @staticmethod
    def reactivate_user(user):
        """Reactivate a user account."""
        user.is_active = True
        user.save()
        return user
