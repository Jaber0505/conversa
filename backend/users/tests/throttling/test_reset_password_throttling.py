import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_password_reset_throttle_exceeded(api_client, user, settings):
    # Assure-toi que le scope "reset_password" est bien configuré
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["reset_password"] = "2/minute"

    url = reverse("reset-password")
    payload = {"email": user.email}

    # 2 premières requêtes → autorisées
    for i in range(2):
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK

    # 3ᵉ requête → trop de tentatives
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "detail" in response.data
    assert "trop de tentatives" in response.data["detail"].lower()
