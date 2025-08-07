import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.SimpleRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "reset_password": "5/min",
        },
    }
)
@pytest.mark.django_db
def test_password_reset_throttling_exceeded(api_client):
    url = reverse("reset-password")
    email = {"email": "spam@example.com"}

    for _ in range(5):
        response = api_client.post(url, email)
        assert response.status_code == 200

    response = api_client.post(url, email)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
