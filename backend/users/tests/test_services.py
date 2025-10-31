"""Tests for User services."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from languages.models import Language
from users.services import AuthService, UserService
from users.models import RevokedAccessToken

User = get_user_model()


class AuthServiceTests(TestCase):
    """Test AuthService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            age=25,
        )

    def test_login_with_valid_credentials(self):
        """Test successful login returns user and tokens."""
        user, refresh, access = AuthService.login("test@example.com", "testpass123")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(access)

    def test_login_with_invalid_credentials(self):
        """Test failed login returns None."""
        user, refresh, access = AuthService.login("test@example.com", "wrongpass")

        self.assertIsNone(user)
        self.assertIsNone(refresh)
        self.assertIsNone(access)

    def test_logout_revokes_tokens(self):
        """Test logout blacklists refresh and revokes access."""
        refresh_token = RefreshToken.for_user(self.user)
        access_token = refresh_token.access_token

        success, error = AuthService.logout(str(refresh_token), str(access_token))

        self.assertTrue(success)
        self.assertIsNone(error)

        # Check access token is revoked
        jti = access_token["jti"]
        self.assertTrue(RevokedAccessToken.objects.filter(jti=jti).exists())

    def test_generate_tokens_for_user(self):
        """Test token generation."""
        refresh, access = AuthService.generate_tokens_for_user(self.user)

        self.assertIsNotNone(refresh)
        self.assertIsNotNone(access)

    def test_is_access_token_revoked(self):
        """Test checking if token is revoked."""
        # Not revoked initially
        self.assertFalse(AuthService.is_access_token_revoked("test-jti"))

        # Revoke it
        RevokedAccessToken.objects.create(jti="test-jti")

        # Now it's revoked
        self.assertTrue(AuthService.is_access_token_revoked("test-jti"))


class UserServiceTests(TestCase):
    """Test UserService."""

    def setUp(self):
        """Set up test data."""
        self.lang_fr = Language.objects.create(code="fr", label_en="French", label_fr="Français", label_nl="Frans", is_active=True)
        self.lang_en = Language.objects.create(code="en", label_en="English", label_fr="Anglais", label_nl="Engels", is_active=True)

    def test_create_user_with_valid_data(self):
        """Test creating user via service."""
        user = UserService.create_user(
            email="new@example.com",
            password="securepass123",
            first_name="New",
            last_name="User",
            age=22,
            native_langs=[self.lang_fr],
            target_langs=[self.lang_en],
            consent_given=True,
        )

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.age, 22)
        self.assertTrue(user.consent_given)
        self.assertIn(self.lang_fr, user.native_langs.all())
        self.assertIn(self.lang_en, user.target_langs.all())

    def test_create_user_underage_fails(self):
        """Test creating user under 18 fails."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="kid@example.com",
                password="pass",
                first_name="Kid",
                last_name="User",
                age=16,
                native_langs=[self.lang_fr],
                target_langs=[self.lang_en],
                consent_given=True,
            )

        self.assertIn("age", cm.exception.detail)

    def test_create_user_without_consent_fails(self):
        """Test creating user without consent fails."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="test@example.com",
                password="pass",
                first_name="Test",
                last_name="User",
                age=25,
                native_langs=[self.lang_fr],
                target_langs=[self.lang_en],
                consent_given=False,
            )

        self.assertIn("consent_given", cm.exception.detail)

    def test_update_user_profile(self):
        """Test updating user profile."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        updated_user = UserService.update_user_profile(
            user, bio="New bio", city="Brussels"
        )

        self.assertEqual(updated_user.bio, "New bio")
        self.assertEqual(updated_user.city, "Brussels")

    def test_update_user_profile_blocks_sensitive_fields(self):
        """Test that sensitive fields raise ValidationError."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        # Try to update sensitive fields - should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            UserService.update_user_profile(
                user,
                is_staff=True,
                is_superuser=True,
                password="hacked",
                email="hacker@evil.com",
                bio="Legit bio change"
            )

        # Check error message mentions unauthorized fields
        self.assertIn("fields", cm.exception.detail)
        error_msg = cm.exception.detail["fields"]
        self.assertIn("email", str(error_msg))
        self.assertIn("is_staff", str(error_msg))
        self.assertIn("is_superuser", str(error_msg))
        self.assertIn("password", str(error_msg))

        # Verify nothing was changed in DB
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("pass"))
        self.assertEqual(user.bio, "")  # Bio was NOT updated

    def test_deactivate_user(self):
        """Test deactivating user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        UserService.deactivate_user(user)

        self.assertFalse(user.is_active)

    def test_reactivate_user(self):
        """Test reactivating user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )
        user.is_active = False
        user.save()

        UserService.reactivate_user(user)

        self.assertTrue(user.is_active)
