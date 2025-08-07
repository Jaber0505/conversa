import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_login_throttle_exceeded(api_client, user, settings):
    # S'assurer que la limite est bien en place pour le test
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"] = "3/minute"

    url = reverse("token_obtain_pair")
    payload = {
        "email": user.email,
        "password": "WrongPassword"
    }

    # Effectuer 4 tentatives invalides
    for i in range(3):
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Mauvais identifiants

    # 4ème tentative doit être bloquée (HTTP 429)
    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
