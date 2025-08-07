import pytest
from django.urls import reverse
from rest_framework import status
from django.test import override_settings


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.UserRateThrottle",
            "rest_framework.throttling.AnonRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "user": "100/min",
            "anon": "10/min",
            "login": "3/seconds",
        },
    }
)
@pytest.mark.django_db
def test_login_throttle_exceeded(api_client, user):
    url = reverse("token_obtain_pair")
    payload = {"email": user.email, "password": "WrongPassword"}

    for _ in range(3):
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
