import pytest
import datetime
from django.utils import timezone
from rest_framework.test import APIClient
from users.models import User

# =============================================================================
# Throttling global pour tous les tests (login, reset_password, etc.)
# =============================================================================

@pytest.fixture(autouse=True, scope="function")
def global_throttle_override(settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "rest_framework.throttling.SimpleRateThrottle",
    ]
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "login": "10/minute",
        "reset_password": "10/minute",
    }

# =============================================================================
# Utilisateurs & clients API
# =============================================================================

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
    user = User(**user_data)
    user.set_password(user_data["password"])
    user.save()
    return user


@pytest.fixture
def superuser(db):
    superuser = User.objects.create_superuser(
        email="admin@example.com",
        password="Admin1234!",
        first_name="Admin",
        last_name="User",
        birth_date=timezone.now().date() - datetime.timedelta(days=365 * 30),
        language_native="fr",
        consent_given=True,
    )
    superuser.set_password("Admin1234!")
    superuser.save()
    return superuser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    response = client.post("/api/auth/token/", {
        "email": user.email,
        "password": "MotDePasse123"
    }, format="json")

    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.content}"
    assert "access" in response.data, f"Response missing 'access': {response.data}"

    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def superuser_client(superuser):
    client = APIClient()
    response = client.post("/api/auth/token/", {
        "email": superuser.email,
        "password": "Admin1234!"
    }, format="json")

    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.content}"
    assert "access" in response.data, f"Response missing 'access': {response.data}"

    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
