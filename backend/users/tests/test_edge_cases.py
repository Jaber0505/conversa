"""
Edge case tests for Users module.

Tests boundary conditions and validation rules.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from languages.models import Language
from users.services import UserService

User = get_user_model()


class UserAgeEdgeCasesTest(TestCase):
    """Test edge cases for user age validation (minimum 18)."""

    def setUp(self):
        """Create test fixtures."""
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_create_user_age_17_should_fail(self):
        """User with age 17 should fail (below minimum 18)."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="minor@example.com",
                password="testpass123",
                age=17,  # Too young!
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

        self.assertIn("18", str(cm.exception))

    def test_create_user_age_18_exactly_should_pass(self):
        """User with age 18 exactly should pass (minimum age)."""
        user = UserService.create_user(
            email="adult@example.com",
            password="testpass123",
            age=18,  # Exactly minimum
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.age, 18)

    def test_create_user_age_100_should_pass(self):
        """User with age 100 should pass (no maximum age limit)."""
        user = UserService.create_user(
            email="senior@example.com",
            password="testpass123",
            age=100,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.age, 100)

    def test_create_user_age_0_should_fail(self):
        """User with age 0 should fail."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="baby@example.com",
                password="testpass123",
                age=0,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

        self.assertIn("18", str(cm.exception))

    def test_create_user_negative_age_should_fail(self):
        """User with negative age should fail."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="invalid@example.com",
                password="testpass123",
                age=-5,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

        self.assertIn("18", str(cm.exception))


class UserLanguagesEdgeCasesTest(TestCase):
    """Test edge cases for user language requirements."""

    def setUp(self):
        """Create test fixtures."""
        self.french = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )
        self.english = Language.objects.create(
            code="en",
            label_fr="Anglais",
            label_en="English",
            label_nl="Engels",
            is_active=True,
        )
        self.dutch = Language.objects.create(
            code="nl",
            label_fr="Néerlandais",
            label_en="Dutch",
            label_nl="Nederlands",
            is_active=True,
        )

    def test_create_user_without_native_languages_should_fail(self):
        """User without native languages should fail."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="test@example.com",
                password="testpass123",
                age=25,
                native_languages=[],  # Empty!
                target_languages=[self.french],
                consent_given=True,
            )

        self.assertIn("at least one native language", str(cm.exception).lower())

    def test_create_user_without_target_languages_should_fail(self):
        """User without target languages should fail."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="test@example.com",
                password="testpass123",
                age=25,
                native_languages=[self.french],
                target_languages=[],  # Empty!
                consent_given=True,
            )

        self.assertIn("at least one target language", str(cm.exception).lower())

    def test_create_user_with_one_native_one_target_should_pass(self):
        """User with exactly 1 native and 1 target should pass (minimum)."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.french],
            target_languages=[self.english],
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.native_languages.count(), 1)
        self.assertEqual(user.target_languages.count(), 1)

    def test_create_user_with_multiple_native_languages_should_pass(self):
        """User can have multiple native languages."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.french, self.english],  # Bilingual
            target_languages=[self.dutch],
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.native_languages.count(), 2)

    def test_create_user_with_multiple_target_languages_should_pass(self):
        """User can have multiple target languages."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.french],
            target_languages=[self.english, self.dutch],  # Learning 2 languages
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.target_languages.count(), 2)


class UserConsentEdgeCasesTest(TestCase):
    """Test edge cases for GDPR consent validation."""

    def setUp(self):
        """Create test fixtures."""
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_create_user_without_consent_should_fail(self):
        """User without consent_given should fail (GDPR required)."""
        with self.assertRaises(ValidationError) as cm:
            UserService.create_user(
                email="test@example.com",
                password="testpass123",
                age=25,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=False,  # No consent!
            )

        self.assertIn("consent", str(cm.exception).lower())

    def test_create_user_with_consent_should_pass(self):
        """User with consent_given=True should pass."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        self.assertIsNotNone(user)
        self.assertTrue(user.consent_given)


class UserEmailEdgeCasesTest(TestCase):
    """Test edge cases for email validation."""

    def setUp(self):
        """Create test fixtures."""
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_create_user_with_duplicate_email_should_fail(self):
        """User with duplicate email should fail (unique constraint)."""
        # Create first user
        UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        # Try to create second user with same email
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserService.create_user(
                email="test@example.com",  # Duplicate!
                password="different_password",
                age=30,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

    def test_create_user_with_empty_email_should_fail(self):
        """User with empty email should fail."""
        with self.assertRaises(ValueError):
            UserService.create_user(
                email="",  # Empty!
                password="testpass123",
                age=25,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

    def test_create_user_with_valid_email_formats_should_pass(self):
        """Various valid email formats should pass."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.com",
        ]

        for email in valid_emails:
            user = UserService.create_user(
                email=email,
                password="testpass123",
                age=25,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )
            self.assertIsNotNone(user)
            self.assertEqual(user.email, email)


class UserPasswordEdgeCasesTest(TestCase):
    """Test edge cases for password validation."""

    def setUp(self):
        """Create test fixtures."""
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_create_user_with_empty_password_should_fail(self):
        """User with empty password should fail."""
        with self.assertRaises(ValueError):
            UserService.create_user(
                email="test@example.com",
                password="",  # Empty!
                age=25,
                native_languages=[self.language],
                target_languages=[self.language],
                consent_given=True,
            )

    def test_create_user_password_is_hashed(self):
        """User password should be hashed (not plain text)."""
        user = UserService.create_user(
            email="test@example.com",
            password="plaintext_password",
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        # Password should NOT be stored as plain text
        self.assertNotEqual(user.password, "plaintext_password")
        # Should be hashed (Django format: algorithm$salt$hash)
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_create_user_with_short_password_should_pass(self):
        """Short passwords are allowed (Django validators can be configured separately)."""
        # By default, UserService doesn't enforce password complexity
        user = UserService.create_user(
            email="test@example.com",
            password="123",  # Very short
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        self.assertIsNotNone(user)


class UserActiveStatusEdgeCasesTest(TestCase):
    """Test edge cases for user active status."""

    def setUp(self):
        """Create test fixtures."""
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_newly_created_user_should_be_active(self):
        """Newly created users should be active by default."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        self.assertTrue(user.is_active)

    def test_deactivated_user_cannot_login(self):
        """Deactivated users should not be able to login."""
        user = UserService.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            native_languages=[self.language],
            target_languages=[self.language],
            consent_given=True,
        )

        # Deactivate user
        user.is_active = False
        user.save()

        # Try to login
        from users.services import AuthService
        with self.assertRaises(ValidationError) as cm:
            AuthService.login(email="test@example.com", password="testpass123")

        self.assertIn("inactive", str(cm.exception).lower())
