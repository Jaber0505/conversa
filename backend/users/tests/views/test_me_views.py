import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_me_view_authenticated_get(auth_client, user):
    url = reverse("user-me")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.data

    expected_fields = {
        "id", "email", "first_name", "last_name",
        "bio", "language_native", "languages_spoken",
        "date_joined", "is_profile_public", "links"
    }

    assert set(data.keys()) == expected_fields
    assert data["email"] == user.email


@pytest.mark.django_db
def test_me_view_patch_update(auth_client, user):
    url = reverse("user-me")
    payload = {
        "first_name": "NouveauPrénom",
        "bio": "Bio mise à jour",
        "languages_spoken": ["es", "it"]
    }

    response = auth_client.patch(url, data=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data["first_name"] == "NouveauPrénom"
    assert data["bio"] == "Bio mise à jour"
    assert set(data["languages_spoken"]) == {"es", "it"}

    user.refresh_from_db()
    assert user.first_name == "NouveauPrénom"
    assert user.bio == "Bio mise à jour"
    assert user.languages_spoken == ["es", "it"]


@pytest.mark.django_db
def test_me_view_unauthenticated_get(api_client):
    url = reverse("user-me")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_me_view_unauthenticated_patch(api_client):
    url = reverse("user-me")
    payload = {"first_name": "Invalide"}
    response = api_client.patch(url, data=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_me_view_delete_anonymises_user(auth_client, user):
    url = reverse("user-me")
    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_200_OK
    assert "supprimé" in response.data["detail"].lower()

    user.refresh_from_db()
    assert user.is_active is False
    assert user.email.startswith("deleted_")
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.bio == ""
    assert user.languages_spoken == []
    assert user.is_profile_public is False
    assert user.consent_given is False
