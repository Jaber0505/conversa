import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_public_user_profile_visible(api_client, user):
    user.is_profile_public = True
    user.save()

    url = reverse("user-public", kwargs={"pk": user.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.data

    expected_fields = {
        "id", "first_name", "last_name",
        "age", "language_native", "languages_spoken", "bio"
    }

    assert set(data.keys()) == expected_fields
    assert data["id"] == user.id
    assert data["first_name"] == user.first_name
    assert isinstance(data["age"], int)


@pytest.mark.django_db
def test_public_user_profile_private(api_client, user):
    user.is_profile_public = False
    user.save()

    url = reverse("user-public", kwargs={"pk": user.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "profil" in response.data["detail"].lower()


@pytest.mark.django_db
def test_public_user_profile_not_found(api_client):
    url = reverse("user-public", kwargs={"pk": 9999})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "profil" in response.data["detail"].lower()
