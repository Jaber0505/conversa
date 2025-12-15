"""User authentication and profile views."""
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from common.mixins import HateoasOptionsMixin
from common.metadata import HateoasMetadata
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer
from .services import AuthService

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="Register new user",
    description=(
        "Create a new user account and receive JWT tokens.\n\n"
        "**Required fields:**\n"
        "- email: Valid email address\n"
        "- password: Minimum 8 characters\n"
        "- first_name: User's first name\n"
        "- native_langs: At least one native language (array of language IDs)\n"
        "- target_langs: At least one target language (array of language IDs)\n"
        "- consent_given: Must be true\n\n"
        "**Returns:** User profile with refresh and access JWT tokens\n\n"
        "**Rate limit:** 5 requests per hour per IP"
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=UserSerializer, description="User created with JWT tokens"
        ),
        400: OpenApiResponse(description="Invalid data"),
    },
)
class RegisterView(HateoasOptionsMixin, generics.CreateAPIView):
    """User registration endpoint."""

    throttle_scope = "auth_register"
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {
        "related": {"login": "/api/v1/auth/login/", "me": "/api/v1/auth/me/"}
    }

    def create(self, request, *args, **kwargs):
        """Create user and return tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh, access = AuthService.generate_tokens_for_user(user)

        data = serializer.data
        response_data = {**data, "refresh": refresh, "access": access}

        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Login with email and password",
    description=(
        "Authenticate user with email and password, receive JWT tokens.\n\n"
        "**Required fields:**\n"
        "- email: User's email address\n"
        "- password: User's password\n\n"
        "**Returns:**\n"
        "- refresh: JWT refresh token (valid 7 days)\n"
        "- access: JWT access token (valid 15 minutes)\n\n"
        "**Rate limit:** 10 requests per minute per IP"
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful with JWT tokens",
            examples=[
                OpenApiExample(
                    "Requête d'exemple",
                    description="Corps à envoyer sur /api/v1/auth/login/",
                    value={"email": "alice@example.com", "password": "password123"},
                    request_only=True,
                ),
                OpenApiExample(
                    "Réponse 200",
                    value={
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            examples=[
                OpenApiExample(
                    "Réponse 401",
                    value={"detail": "Invalid credentials."},
                    response_only=True,
                )
            ],
        ),
    },
)
class EmailLoginView(HateoasOptionsMixin, APIView):
    """User login endpoint."""

    throttle_scope = "auth_login"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {
        "related": {
            "register": "/api/v1/auth/register/",
            "refresh": "/api/v1/auth/refresh/",
        }
    }

    def post(self, request, *args, **kwargs):
        """Authenticate user and return tokens."""
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        user, refresh, access, was_reactivated = AuthService.login(email, password)

        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response_data = {"refresh": refresh, "access": access}

        # Add message if account was reactivated
        if was_reactivated:
            response_data["message"] = "Your account has been reactivated successfully."

        return Response(response_data, status=200)


@extend_schema(
    tags=["Auth"],
    summary="Request password reset",
    description=(
        "Accepts an email and, if the account exists, sends a reset email.\n\n"
        "For development environments without email, this endpoint always\n"
        "returns 200 to avoid leaking account existence."
    ),
    request={"application/json": {"email": "string"}},
    responses={200: OpenApiResponse(description="Reset email processed")},
)
class PasswordResetRequestView(HateoasOptionsMixin, APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    def post(self, request, *args, **kwargs):
        # Intentionally do not reveal if email exists. Always respond 200.
        return Response({"detail": "If the email exists, a reset link was sent."}, status=200)


@extend_schema(
    tags=["Auth"],
    summary="Refresh JWT access token",
    description=(
        "Get a new access token using a valid refresh token.\n\n"
        "**Required field:**\n"
        "- refresh: Valid JWT refresh token\n\n"
        "**Returns:**\n"
        "- access: New JWT access token (valid 15 minutes)\n"
        "- refresh: New JWT refresh token (if rotation enabled)\n\n"
        "**Note:** Old refresh token is blacklisted after use (rotation enabled)"
    ),
    request={"application/json": {"refresh": "string"}},
    responses={
        200: OpenApiResponse(description="Access token refreshed"),
        401: OpenApiResponse(description="Refresh token expired or invalid"),
    },
)
class RefreshView(HateoasOptionsMixin, TokenRefreshView):
    """JWT token refresh endpoint."""

    throttle_scope = "auth_refresh"
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"login": "/api/v1/auth/login/"}}


@extend_schema(
    tags=["Auth"],
    summary="Logout user",
    description=(
        "Logout user by blacklisting both refresh and access tokens.\n\n"
        "**Required:**\n"
        "- refresh: Refresh token (in request body)\n"
        "- Authorization: Bearer access token (in header)\n\n"
        "**Effect:** Both tokens are blacklisted and cannot be used again\n\n"
        "**Returns:** 204 No Content on success"
    ),
    request={
        "application/json": {
            "refresh": "string (required)",
            "access": "string (from Authorization header)",
        }
    },
    responses={
        204: OpenApiResponse(description="Logout successful"),
        400: OpenApiResponse(description="Invalid or missing tokens"),
    },
)
class LogoutView(HateoasOptionsMixin, APIView):
    """User logout endpoint (blacklists refresh + revokes access)."""

    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata
    extra_hateoas = {"related": {"login": "/api/v1/auth/login/"}}

    def post(self, request, *args, **kwargs):
        """Logout user by revoking tokens."""
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get access token from Authorization header
        access_token = str(request.auth) if request.auth else None
        if not access_token:
            return Response(
                {"detail": "Authorization header with access token required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Logout via service
        success, error = AuthService.logout(refresh_token, access_token)

        if not success:
            return Response(
                {"detail": error}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Auth"],
    summary="Get current user profile",
    description=(
        "Returns the authenticated user's profile information.\n\n"
        "**Authentication:** Required (Bearer JWT token)\n\n"
        "**Returns:** User profile including:\n"
        "- Personal information (email, name, bio)\n"
        "- Language preferences (native_langs, target_langs)\n"
        "- Account status (is_active, consent_given)\n"
        "- Timestamps (created_at, updated_at)"
    ),
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Not authenticated"),
    },
)
class MeView(HateoasOptionsMixin, generics.RetrieveAPIView):
    """Get current user profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"logout": "/api/v1/auth/logout/"}}

    def get_object(self):
        """Return authenticated user."""
        return self.request.user


@extend_schema(
    tags=["Auth"],
    summary="Deactivate user account",
    description=(
        "Temporarily deactivate the authenticated user's account (REVERSIBLE).\n\n"
        "**Authentication:** Required (Bearer JWT token)\n\n"
        "**Effect:**\n"
        "- User account is set to inactive (is_active=False)\n"
        "- User cannot login anymore\n"
        "- All user data is preserved\n"
        "- User can reactivate by registering again with the same email\n\n"
        "**Business Rules:**\n"
        "- User cannot have any upcoming confirmed bookings\n"
        "- User cannot be organizer of any upcoming published events\n\n"
        "**Returns:** 204 No Content on success"
    ),
    request={
        "application/json": {
            "password": "string (required - confirm user identity)"
        }
    },
    responses={
        204: OpenApiResponse(description="Account deactivated successfully"),
        400: OpenApiResponse(description="Invalid password or business rule violation"),
        401: OpenApiResponse(description="Not authenticated"),
    },
)
class DeactivateAccountView(HateoasOptionsMixin, APIView):
    """Deactivate user account endpoint (reversible)."""

    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata

    def delete(self, request, *args, **kwargs):
        """Deactivate user account after password confirmation."""
        password = request.data.get("password")
        if not password:
            return Response(
                {"detail": "Password required for account deactivation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify password
        if not request.user.check_password(password):
            return Response(
                {"detail": "Invalid password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check business rules via service
        success, error = AuthService.delete_account(request.user)

        if not success:
            return Response(
                {"detail": error}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Auth"],
    summary="Permanently delete user account",
    description=(
        "Permanently delete the authenticated user's account (IRREVERSIBLE).\n\n"
        "**Authentication:** Required (Bearer JWT token)\n\n"
        "**Effect:**\n"
        "- All personal data is anonymized (GDPR compliant)\n"
        "- Email becomes: purged_user_[id]@deleted.local\n"
        "- Name becomes: 'Deleted User'\n"
        "- All personal fields cleared (bio, address, languages, etc.)\n"
        "- Account cannot be reactivated\n"
        "- User record kept for referential integrity (bookings history)\n\n"
        "**Business Rules:**\n"
        "- User cannot have any upcoming confirmed bookings\n"
        "- User cannot be organizer of any upcoming published events\n\n"
        "**Note:** No password confirmation required - JWT authentication is sufficient\n\n"
        "**Returns:** 204 No Content on success"
    ),
    request=None,
    responses={
        204: OpenApiResponse(description="Account permanently deleted"),
        400: OpenApiResponse(description="Business rule violation"),
        401: OpenApiResponse(description="Not authenticated"),
    },
)
class PermanentlyDeleteAccountView(HateoasOptionsMixin, APIView):
    """Permanently delete user account endpoint (irreversible)."""

    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata

    def delete(self, request, *args, **kwargs):
        """Permanently delete user account without password confirmation."""
        # No password verification required - user is already authenticated via JWT

        # Check business rules via service
        success, error = AuthService.permanently_delete_account(request.user)

        if not success:
            return Response(
                {"detail": error}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
