"""Custom JWT authentication with access token denylist."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .services import AuthService


class JWTAuthenticationWithDenylist(JWTAuthentication):
    """
    JWT authentication with revoked token checking.

    Extends SimpleJWT's default authentication to check if access tokens
    have been explicitly revoked (e.g., during logout).
    """

    def get_validated_token(self, raw_token):
        """
        Validate token and check denylist.

        Args:
            raw_token: Raw JWT token bytes

        Returns:
            Token: Validated token object

        Raises:
            InvalidToken: If token is invalid or revoked
        """
        token = super().get_validated_token(raw_token)
        jti = token.get("jti")

        if jti and AuthService.is_access_token_revoked(jti):
            raise InvalidToken("Access token has been revoked.")

        return token
