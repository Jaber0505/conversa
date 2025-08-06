import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

@pytest.mark.django_db
def test_me_view_blocks_inactive_user(auth_client, user):
    user.is_active = False
    user.save()

    response = auth_client.get("/api/me/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_get_me(auth_client):
    response = auth_client.get("/api/users/me/")
    assert response.status_code == 200
    assert "email" in response.data


@pytest.mark.django_db
def test_patch_me(auth_client):
    response = auth_client.patch("/api/users/me/", {"first_name": "Updated"})
    assert response.status_code == 200
    assert response.data["detail"] == "Profil mis à jour."


@pytest.mark.django_db
def test_delete_me(auth_client):
    response = auth_client.delete("/api/users/me/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_get_me_unauthenticated(client):
    response = client.get("/api/users/me/")
    assert response.status_code == 401
