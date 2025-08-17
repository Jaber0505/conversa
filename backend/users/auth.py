from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import RevokedAccessToken

class JWTAuthenticationWithDenylist(JWTAuthentication):
    """
    Auth JWT + denylist d'access tokens (JTI).
    Si le token est révoqué, on renvoie 401 (InvalidToken).
    """
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        jti = token.get("jti")
        if jti and RevokedAccessToken.objects.filter(jti=jti).exists():
            raise InvalidToken("Access token revoked.")
        return token
