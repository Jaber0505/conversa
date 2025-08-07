import pytest
from rest_framework import status
from django.urls import reverse


@pytest.mark.django_db
def test_export_data_view_authenticated(auth_client, user):
    url = reverse("user-export")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "export" in response.data

    export_data = response.data["export"]

    expected_fields = {
        "id",
        "email",
        "first_name",
        "last_name",
        "bio",
        "language_native",
        "languages_spoken",
        "date_joined",
        "is_profile_public",
        "links",
    }

    assert set(export_data.keys()) == expected_fields
    assert export_data["email"] == user.email


@pytest.mark.django_db
def test_export_data_view_unauthenticated(api_client):
    url = reverse("user-export")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
