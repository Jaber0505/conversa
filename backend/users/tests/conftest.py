import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from users.models import User
import datetime


@pytest.fixture
def user_data():
    return {
        "email": "testuser@example.com",
        "password": "MotDePasse123",
        "first_name": "Jean",
        "last_name": "Dupont",
        "birth_date": timezone.now().date() - datetime.timedelta(days=365 * 25),
        "language_native": "fr",
        "languages_spoken": ["en", "nl"],
        "bio": "Utilisateur de test",
        "consent_given": True,
    }


@pytest.fixture
def user(db, user_data):
    """Crée un utilisateur actif avec mot de passe valide."""
    return User.objects.create_user(**user_data)


@pytest.fixture
def superuser(db):
    """Crée un superutilisateur."""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="Admin1234!",
        first_name="Admin",
        last_name="User",
        birth_date=timezone.now().date() - datetime.timedelta(days=365 * 30),
        language_native="fr",
        consent_given=True,
    )


@pytest.fixture
def api_client():
    """Client API non authentifié (visiteur)."""
    return APIClient()


@pytest.fixture
def auth_client(user):
    """Client API authentifié avec utilisateur normal."""
    client = APIClient()
    response = client.post("/api/auth/token/", {
        "email": user.email,
        "password": "MotDePasse123"
    }, format="json")
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.content}"
    return client


@pytest.fixture
def superuser_client(superuser):
    """Client API authentifié avec superutilisateur."""
    client = APIClient()
    response = client.post("/api/auth/token/", {
        "email": superuser.email,
        "password": "Admin1234!"
    }, format="json")
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.content}"
    return client
