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
    def login(email, password):
        """
        Authenticate user and generate JWT tokens.

        Args:
            email: User's email address
            password: User's password

        Returns:
            tuple: (user, refresh_token, access_token) if successful
            tuple: (None, None, None) if authentication fails

        Example:
            user, refresh, access = AuthService.login("user@example.com", "password")
            if user:
                # Login successful
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        email = (email or "").strip()
        user = authenticate(username=email, password=password)

        if not user:
            return None, None, None

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return user, str(refresh), str(access)

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
