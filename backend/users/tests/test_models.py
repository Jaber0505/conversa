"""Tests for User models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from languages.models import Language
from users.models import UserTargetLanguage, RevokedAccessToken

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model."""

    def setUp(self):
        """Set up test data."""
        self.language_fr = Language.objects.create(
            code="fr", label_en="French", label_fr="Français", label_nl="Frans", is_active=True
        )
        self.language_en = Language.objects.create(
            code="en", label_en="English", label_fr="Anglais", label_nl="Engels", is_active=True
        )

    def test_create_user(self):
        """Test creating a user with valid data."""
        user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
            first_name="Test",
            last_name="User",
            age=25,
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("securepass123"))
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.age, 25)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_user_without_email_fails(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="", password="pass", first_name="Test", last_name="User", age=20
            )

        self.assertIn("Email is required", str(cm.exception))

    def test_create_user_without_password_fails(self):
        """Test creating user without password raises error."""
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="test@example.com",
                password="",
                first_name="Test",
                last_name="User",
                age=20,
            )

        self.assertIn("Password is required", str(cm.exception))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            first_name="Admin",
            last_name="User",
            age=30,
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_full_name_property(self):
        """Test full_name property."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
            last_name="Doe",
            age=25,
        )

        self.assertEqual(user.full_name, "John Doe")

    def test_user_languages(self):
        """Test adding languages to user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        user.native_langs.add(self.language_fr)
        user.target_langs.add(self.language_en)

        self.assertIn(self.language_fr, user.native_langs.all())
        self.assertIn(self.language_en, user.target_langs.all())

    def test_duplicate_email_fails(self):
        """Test creating user with duplicate email fails."""
        User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="test@example.com",
                password="pass2",
                first_name="Another",
                last_name="User",
                age=30,
            )


class UserTargetLanguageTests(TestCase):
    """Test UserTargetLanguage through model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )
        self.language = Language.objects.create(
            code="es", label_en="Spanish", label_fr="Espagnol", label_nl="Spaans", is_active=True
        )

    def test_create_user_target_language(self):
        """Test creating user-language relationship."""
        utl = UserTargetLanguage.objects.create(
            user=self.user, language=self.language
        )

        self.assertEqual(str(utl), f"{self.user.email} learning {self.language.label_en}")

    def test_unique_together_constraint(self):
        """Test user-language pair must be unique."""
        UserTargetLanguage.objects.create(user=self.user, language=self.language)

        with self.assertRaises(IntegrityError):
            UserTargetLanguage.objects.create(user=self.user, language=self.language)


class RevokedAccessTokenTests(TestCase):
    """Test RevokedAccessToken model."""

    def test_create_revoked_token(self):
        """Test creating revoked token entry."""
        token = RevokedAccessToken.objects.create(jti="test-jti-12345")

        self.assertEqual(token.jti, "test-jti-12345")
        self.assertIsNotNone(token.revoked_at)

    def test_str_representation(self):
        """Test string representation shows JTI preview."""
        token = RevokedAccessToken.objects.create(jti="test-jti-12345")

        self.assertIn("Revoked test-jti", str(token))
