"""Tests for User views."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from languages.models import Language

User = get_user_model()


class RegisterViewTests(TestCase):
    """Test user registration endpoint."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.url = reverse("auth-register")

        self.lang_fr = Language.objects.create(code="fr", label_en="French", label_fr="Français", label_nl="Frans", is_active=True)
        self.lang_en = Language.objects.create(code="en", label_en="English", label_fr="Anglais", label_nl="Engels", is_active=True)

    def test_register_with_valid_data(self):
        """Test successful user registration."""
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

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_without_consent_fails(self):
        """Test registration without consent fails."""
        data = {
            "email": "test@example.com",
            "password": "pass",
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
            "native_langs": ["fr"],
            "target_langs": ["en"],
            "consent_given": False,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailLoginViewTests(TestCase):
    """Test user login endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.url = reverse("auth-login")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            age=25,
        )

    def test_login_with_valid_credentials(self):
        """Test successful login."""
        data = {"email": "test@example.com", "password": "testpass123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_credentials(self):
        """Test login with wrong password fails."""
        data = {"email": "test@example.com", "password": "wrongpass"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTests(TestCase):
    """Test user logout endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.url = reverse("auth-logout")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

        self.refresh = RefreshToken.for_user(self.user)
        self.access = str(self.refresh.access_token)

    def test_logout_with_valid_tokens(self):
        """Test successful logout."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        data = {"refresh": str(self.refresh)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_without_refresh_token_fails(self):
        """Test logout without refresh token fails."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeViewTests(TestCase):
    """Test current user profile endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.url = reverse("auth-me")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="Test",
            last_name="User",
            age=25,
        )

    def test_get_me_authenticated(self):
        """Test getting current user profile when authenticated."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_get_me_unauthenticated_fails(self):
        """Test getting profile without authentication fails."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
