import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_password_reset_throttling_exceeded(api_client, settings):
    url = reverse("reset-password")
    email = {"email": "spam@example.com"}

    for _ in range(5):
        response = api_client.post(url, email)
        assert response.status_code == 200

    response = api_client.post(url, email)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
