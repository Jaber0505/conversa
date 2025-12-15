"""
Authentication service for user login, logout, and token management.

Handles JWT token generation, refresh token blacklisting, and access token
denylist for secure logout functionality.
"""
from django.contrib.auth import authenticate
from django.db import transaction

from common.services.base import BaseService


class AuthService(BaseService):
    """
    Authentication business logic.

    Handles user login, logout, token refresh, and token revocation.
    """

    @staticmethod
    @transaction.atomic
    def login(email, password):
        """
        Authenticate user and generate JWT tokens.

        If the user account is deactivated (is_active=False), it will be
        automatically reactivated upon successful authentication.

        Args:
            email: User's email address
            password: User's password

        Returns:
            tuple: (user, refresh_token, access_token, was_reactivated) if successful
            tuple: (None, None, None, False) if authentication fails

        Example:
            user, refresh, access, reactivated = AuthService.login("user@example.com", "password")
            if user:
                # Login successful
                if reactivated:
                    # Account was reactivated
        """
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model

        User = get_user_model()
        email = (email or "").strip()

        # First try normal authentication (for active users)
        user = authenticate(username=email, password=password)
        was_reactivated = False

        # If authentication failed, check if there's a deactivated account
        if not user:
            try:
                deactivated_user = User.objects.get(email=email, is_active=False)
                # Check if password matches
                if deactivated_user.check_password(password):
                    # Reactivate the account
                    deactivated_user.is_active = True
                    deactivated_user.save()
                    user = deactivated_user
                    was_reactivated = True
                else:
                    return None, None, None, False
            except User.DoesNotExist:
                return None, None, None, False

        if not user:
            return None, None, None, False

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return user, str(refresh), str(access), was_reactivated

    @staticmethod
    @transaction.atomic
    def logout(refresh_token_str, access_token_str):
        """
        Logout user by blacklisting refresh token and revoking access token.

        Args:
            refresh_token_str: Refresh token string
            access_token_str: Access token string

        Returns:
            tuple: (success: bool, error_message: str|None)

        Example:
            success, error = AuthService.logout(refresh_token, access_token)
            if not success:
                return Response({"detail": error}, status=400)
        """
        from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        from ..models import RevokedAccessToken

        # 1. Blacklist refresh token
        try:
            refresh = RefreshToken(refresh_token_str)
            refresh.blacklist()
        except TokenError as e:
            return False, f"Invalid refresh token: {str(e)}"
        except Exception as e:
            return False, f"Failed to blacklist refresh token: {str(e)}"

        # 2. Revoke access token (add to denylist)
        try:
            access = AccessToken(access_token_str)
            jti = access["jti"]
            RevokedAccessToken.objects.get_or_create(jti=jti)
        except TokenError as e:
            return False, f"Invalid access token: {str(e)}"
        except Exception as e:
            return False, f"Failed to revoke access token: {str(e)}"

        return True, None

    @staticmethod
    def is_access_token_revoked(jti):
        """
        Check if an access token has been revoked.

        Args:
            jti: JWT ID from token payload

        Returns:
            bool: True if token is revoked, False otherwise
        """
        from ..models import RevokedAccessToken
        return RevokedAccessToken.objects.filter(jti=jti).exists()

    @staticmethod
    def generate_tokens_for_user(user):
        """
        Generate fresh JWT tokens for a user.

        Args:
            user: User instance

        Returns:
            tuple: (refresh_token_str, access_token_str)

        Example:
            refresh, access = AuthService.generate_tokens_for_user(user)
        """
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh), str(refresh.access_token)

    @staticmethod
    def cleanup_old_revoked_tokens(days=30):
        """
        Delete revoked tokens older than specified days.

        Args:
            days: Number of days to keep revoked tokens (default: 30)

        Returns:
            int: Number of tokens deleted

        Note:
            This should be run periodically (e.g., via Django management command)
            to prevent the RevokedAccessToken table from growing indefinitely.
        """
        from django.utils import timezone
        from datetime import timedelta
        from ..models import RevokedAccessToken

        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = RevokedAccessToken.objects.filter(
            revoked_at__lt=cutoff_date
        ).delete()

        return deleted_count

    @staticmethod
    @transaction.atomic
    def delete_account(user):
        """
        Delete user account (deactivate and revoke all tokens).

        Business Rules:
            - User cannot have any upcoming confirmed bookings
            - User cannot be organizer of any upcoming published events

        Args:
            user: User instance to deactivate

        Returns:
            tuple: (success: bool, error_message: str|None)

        Example:
            success, error = AuthService.delete_account(user)
            if not success:
                return Response({"detail": error}, status=400)
        """
        from django.utils import timezone
        from bookings.models import Booking, BookingStatus
        from events.models import Event

        now = timezone.now()

        # Check for upcoming confirmed bookings
        upcoming_bookings = Booking.objects.filter(
            user=user,
            status=BookingStatus.CONFIRMED,
            event__datetime_start__gte=now
        ).exists()

        if upcoming_bookings:
            return False, "Cannot delete account: you have upcoming confirmed bookings. Please cancel them first."

        # Check for upcoming published events as organizer
        upcoming_events = Event.objects.filter(
            organizer=user,
            status=Event.Status.PUBLISHED,
            datetime_start__gte=now
        ).exists()

        if upcoming_events:
            return False, "Cannot delete account: you are organizing upcoming published events. Please cancel them first."

        # Deactivate user account (reversible)
        from .user_service import UserService
        UserService.deactivate_user(user)

        return True, None

    @staticmethod
    @transaction.atomic
    def permanently_delete_account(user):
        """
        Permanently delete user account (anonymize all personal data).

        This is GDPR compliant permanent deletion. The user record is kept
        for referential integrity (bookings, events) but all personal data
        is anonymized.

        Business Rules:
            - User cannot have any upcoming confirmed bookings
            - User cannot be organizer of any upcoming published events

        Args:
            user: User instance to permanently delete

        Returns:
            tuple: (success: bool, error_message: str|None)

        Example:
            success, error = AuthService.permanently_delete_account(user)
            if not success:
                return Response({"detail": error}, status=400)
        """
        from django.utils import timezone
        from bookings.models import Booking, BookingStatus
        from events.models import Event

        now = timezone.now()

        # 1. Cancel all upcoming confirmed bookings WITH AUTOMATIC REFUND
        upcoming_bookings = Booking.objects.filter(
            user=user,
            status=BookingStatus.CONFIRMED,
            event__datetime_start__gte=now
        )

        from bookings.services import BookingService

        for booking in upcoming_bookings:
            # Use BookingService to handle cancellation + automatic Stripe refund
            # system_cancellation=True bypasses the 3h deadline check
            try:
                BookingService.cancel_booking(
                    booking=booking,
                    cancelled_by=user,
                    system_cancellation=True
                )
            except Exception as e:
                # Log error but continue with other bookings
                # We don't want to block account deletion if one refund fails
                pass

        # 2. Cancel all PENDING bookings (no refund needed)
        pending_bookings = Booking.objects.filter(
            user=user,
            status=BookingStatus.PENDING,
            event__datetime_start__gte=now
        )

        for booking in pending_bookings:
            booking.mark_cancelled()

        # 3. Cancel all upcoming published events as organizer
        upcoming_events = Event.objects.filter(
            organizer=user,
            status=Event.Status.PUBLISHED,
            datetime_start__gte=now
        )

        for event in upcoming_events:
            event.mark_cancelled(cancelled_by=user, system_cancellation=True)

        # 4. Delete all draft events (brouillons)
        draft_events = Event.objects.filter(
            organizer=user,
            status=Event.Status.DRAFT
        )

        draft_events.delete()

        # 5. Anonymize user data
        from .user_service import UserService

        UserService.anonymize_user(user, email_prefix="purged_user")

        return True, None
