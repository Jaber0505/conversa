"""Tests for User serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model

from languages.models import Language
from users.serializers import UserSerializer, RegisterSerializer

User = get_user_model()


class UserSerializerTests(TestCase):
    """Test UserSerializer."""

    def setUp(self):
        """Set up test data."""
        self.lang_fr = Language.objects.create(code="fr", label_en="French", label_fr="Français", label_nl="Frans", is_active=True)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )
        self.user.native_langs.add(self.lang_fr)

    def test_serialize_user(self):
        """Test serializing user data."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["age"], 25)
        self.assertIn("fr", data["native_langs"])
        self.assertNotIn("password", data)


class RegisterSerializerTests(TestCase):
    """Test RegisterSerializer."""

    def setUp(self):
        """Set up test data."""
        self.lang_fr = Language.objects.create(code="fr", label_en="French", label_fr="Français", label_nl="Frans", is_active=True)
        self.lang_en = Language.objects.create(code="en", label_en="English", label_fr="Anglais", label_nl="Engels", is_active=True)

    def test_valid_registration_data(self):
        """Test valid registration data."""
        data = {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
            "age": 22,
            "native_langs": ["fr"],
            "target_langs": ["en"],
            "consent_given": True,
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_registration_without_native_langs_fails(self):
        """Test registration without native languages fails."""
        data = {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
            "age": 22,
            "native_langs": [],
            "target_langs": ["en"],
            "consent_given": True,
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("native_langs", serializer.errors)

    def test_registration_without_consent_fails(self):
        """Test registration without consent fails."""
        data = {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
            "age": 22,
            "native_langs": ["fr"],
            "target_langs": ["en"],
            "consent_given": False,
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("consent_given", serializer.errors)

    def test_registration_underage_fails(self):
        """Test registration with age < 18 fails."""
        data = {
            "email": "kid@example.com",
            "password": "pass",
            "first_name": "Kid",
            "last_name": "User",
            "age": 16,
            "native_langs": ["fr"],
            "target_langs": ["en"],
            "consent_given": True,
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("age", serializer.errors)
